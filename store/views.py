from django.shortcuts import redirect, render
from .models import *
from django.http import JsonResponse,HttpResponse
import json
from django.db.models import Q
from django.contrib import messages
from datetime import datetime, timezone
import mail.views as mail
from mail.tasks import invoice_create_send
# Create your views here.

def store(request):
    products = Product.objects.all()
    context={'products': products}
    return render(request, "store/store.html", context)

def search(request):
    q = request.GET['q']
    products = Product.objects.filter(Q(album_name__icontains=q) | Q(artist_name__icontains=q))
    context={'products': products}
    return render(request, 'store/search.html', context)

def category(request,category):
    products = Product.objects.filter(genre__iexact=category)
    context={'products': products}
    return render(request, 'store/category.html', context)

def onSale(request):
    products = Product.objects.filter(onDiscount=True)
    context={'products': products}
    return render(request, 'store/onSale.html', context)

def sortPrice(request):
    products = Product.objects.filter().order_by('price')
    context={'products': products}
    return render(request, 'store/sortPrice.html', context)


def product_detail(request,id):
    product = Product.objects.get(pk=id)
    items = OrderItem.objects.filter(product=product)
    print(items)
    rating= 0
    counter = 0
    avg= 0
    for i in items:
        rating += i.rating
        if(i.rating != 0):
            counter+=1
    if(rating != 0):
        avg = int(rating/counter)
    context={'product': product, 'rating': avg}
    return render(request, "store/product.html", context)

def pastOrders(request):
    if request.user.is_authenticated:
        pastProducts=[]
        user = request.user
        pastOrders = Order.objects.filter(customer = user, isComplete = True, status=3)
        for i in pastOrders:
            pastProducts.append(OrderItem.objects.filter(order=i))
        
        print(pastProducts)
        context={'pastproducts': pastProducts}
        return render(request, "store/past-orders.html", context)

def cart(request):
    if request.user.is_authenticated:
        user = request.user
        order, created = Order.objects.get_or_create(customer = user, isComplete= False)
        items = order.orderitem_set.all()
    
    else: #These are not stored in our database. Nonusers can see these products in their cart page
        try:
            cart = json.loads(request.COOKIES['cart'])
        except:
            cart={}
        #print('Cart:', cart)
        items = []    
        order = {'getCartTotal' : 0 , 'getCartItems' : 0, 'isComplete' : False} #THIS IS JUST TEMPLATE. WILL CHANGE WHEN WE HANDLE NONUSER CART PART
        cartItems = order["getCartItems"]
        for i in cart:
            try:
                cartItems += cart[i]["quantity"]
                product = Product.objects.get(id = i)
                cost = (product.price *cart[i]["quantity"] )
                order['getCartTotal'] += cost
                order['getCartItems'] += cart[i]["quantity"]
                item = {
                    'product' : {
                        'id' : product.id,
                        'album_name' : product.album_name,
                        'artist_name' : product.artist_name,
                        'price' : product.price,
                        'image' : product.image,
                    },
                    'quantity': cart[i]["quantity"],
                    'getTotal' : cost
                }
                items.append(item)
            except: 
                pass
    context={'items' : items, 'order' : order}
    return render(request, "store/cart.html", context)

def checkout(request):
    if request.user.is_authenticated:
        user = request.user
        order, created = Order.objects.get_or_create(customer = user, isComplete= False)
        items = order.orderitem_set.all()
    else:
        cart = json.loads(request.COOKIES['cart'])
        items=[] #KEEP THESE EMPTY FOR NOW. WILL UPDATE LATER ON 
        order = {'getCartTotal' : 0 , 'getCartItems' : 0, 'isComplete' : False}
        cartItems = order["getCartItems"]
        for i in cart:
            try:
                cartItems += cart[i]["quantity"]
                product = Product.objects.get(id = i)
                cost = (product.price *cart[i]["quantity"] )
                order['getCartTotal'] += cost
                order['getCartItems'] += cart[i]["quantity"]
                item = {
                    'product' : {
                        'id' : product.id,
                        'album_name' : product.album_name,
                        'artist_name' : product.artist_name,
                        'price' : product.price,
                        'image' : product.image,
                    },
                    'quantity': cart[i]["quantity"],
                    'getTotal' : cost
                }
                items.append(item)
            except: 
                pass

    context={'items' : items, 'order' : order}
    return render(request, "store/checkout.html", context)

def account(request):
    if request.user.is_authenticated:
        return redirect('profile')
    context={}
    return render(request, "store/account.html", context)


def userUpdateItemInCart(request):
    data = json.loads(request.body)
    productID = data['productID']
    action = data['action']

    customer = request.user
    product = Product.objects.get(id=productID)
    order, created = Order.objects.get_or_create(customer = customer, isComplete=False)
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action =='add':
        order_item.quantity = order_item.quantity +1
        
    elif action == 'remove':
        order_item.quantity = order_item.quantity -1
    
    order_item.save()

    if order_item.quantity <= 0:
        order_item.delete()
    return JsonResponse("Item is added", safe = False)

def processedPayment(request):
    #transaction_id = 
    customer = request.user
    order = Order.objects.get(customer = customer, isComplete = False)
    data = json.loads(request.body)
    shippingForm = data['shippingForm']
    print(shippingForm)
    billingForm = data['billingForm']
    
    shipping = ShippingAdress.objects.create(customer = customer) # get_or_create veya düz create
    shipping.address = shippingForm['address']
    shipping.city = shippingForm['city']
    shipping.state = shippingForm['state']
    shipping.zipcode = shippingForm['zipcode']
    shipping.country = shippingForm['country']
    shipping.order = order

    shipping.save()

    billing, created = CreditCard.objects.get_or_create(customerID = customer)
    billing.cardName = billingForm['ownerName']
    billing.cardNumber = billingForm['CardNo']
    billing.exprDate = billingForm['ExpirationDate']

    billing.save()

    order.isComplete = True
    order.save()

    items =  order.orderitem_set.all()
    for i in items: ##DECREASE THE STOCK OF PURCHASED ITEMS
        i.product.stock = i.product.stock - i.quantity
        print(i.product.stock)
        i.product.save()

    return JsonResponse("Payment Complete", safe=False)

def successfulPayment(request,pk):
    number = pk
    order = Order.objects.get(pk=number)
    items = order.orderitem_set.all()
    shipping = ShippingAdress.objects.get(order=order)
    context={'items' : items, 'order' : order, 'shipping': shipping}
    return render(request, "store/successful.html", context)

def profile(request):
    # if not request.user.is_authenticated:
    #     return redirect('login')
    if request.user.is_authenticated:
        pastProducts=[]
        user = request.user
        pastOrders = Order.objects.filter(customer = user, isComplete = True)
        for i in pastOrders:
            pastProducts.append(OrderItem.objects.filter(order=i))
        
        print(pastProducts)
        context={'pastproducts': pastProducts}
        return render(request, "store/profile.html", context)

    


def addComment(request):
    
    if request.user.is_authenticated:
        if request.method=="POST":
            customer = request.user
            id = request.POST['product']
            product = Product.objects.get(pk=id)
            comment_body = request.POST['userComment']
            comment = Comment(product = product, user=customer, body = comment_body )
            comment.save()
            messages.success(request, 'Hello world.')
            context={'product': product}
            return render(request, "store/product.html", context)
        #return HttpResponse(res)

    
    else:
        #context={'product': product}
        #messages.add_message(request, messages.INFO, 'Hello world.')
        return render(request, "store/product.html", context)
    
def addRating(request):
    #this may be unnecessary
    product = Product.objects.filter(score=0).order_by("?").first()
    context = {'product': product}
    return render(request, "store/product.html", context)

def rate(request, id):
    product = OrderItem.objects.get(id=id)
    context = {'orderItems': product}
    return render(request, "store/rate.html", context)

def add_rating(request):
    if request.method=="POST":
        orderItemID = request.POST.get('el_id')
        print(orderItemID)
        value = request.POST.get('val')
        obj = OrderItem.objects.get(pk=orderItemID)
        obj.rating = value
        obj.save()
        return JsonResponse({'success': 'true' , 'rating': value}, safe=False)

    return JsonResponse({'success': 'false'})

def refund(request,id):
    item = OrderItem.objects.get(pk=id)
    today = datetime.now(timezone.utc)
    diff = (item.order.order_date - today).days
    if diff <= 30:
        #ACCEPT REFUND
        refund, created = Refund.objects.get_or_create(order_item = item)
        refund.onDiscount = item.product.onDiscount
        refund.price = item.product.price
        refund.quantity = item.quantity
        refund.total = item.getTotal
        refund.save()
        item.refund_request = True
        item.save()
    
    return redirect('/profile')

def cancelOrder(request,id):
    item = OrderItem.objects.get(pk=id)
    
    refund, created = Refund.objects.get_or_create(order_item = item)
    refund.onDiscount = item.product.onDiscount
    refund.price = item.product.price
    refund.quantity = item.quantity
    refund.total = item.getTotal
    refund.save()
    item.refund_request = True
    item.save()
    
    return redirect('/profile')

def refundDetail(request, id):
    refund = Refund.objects.get(order_item=id)
    context = {"refund":refund}
    return render(request, "store/refund_detail.html", context)