from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponseNotFound, HttpResponse
from django.utils import timezone
from .models import LabJob, Other, inventory, ordered, Users, categories, Message, POs, shelf
from .forms import BoxForm, user_gen_form, LabJobFormsetNudge, LabJobFormset,  OrderForm, newItemForm, loginForm, OrderReceiveFormset, MessageForm, BulkNewItemFormset, InvenEditForm
from datetime import timedelta, datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.urls import reverse
from PIL import Image, ImageDraw, ImageFont
import ezgmail
import numpy as np
import os
from pytimeparse.timeparse import timeparse
import pytz
import shutil
from collections import Counter
import ast

# Create your views here.
# ####dependencies and Functions
emaildict = {}
inventory1 = inventory.objects.all()
current_inven = list(map(lambda n:n.item_code, inventory1))

colors = {}


def quickOrdered(request, id):
    item = ordered.objects.get(pk=id)
    item.order_ordered = True
    item.order_date = timezone.now() - timedelta(hours=5, minutes=0)
    item.save()
    return redirect('/')

def quickReceived(request, id):
    item = ordered.objects.get(pk=id)
    item.order_received = True
    item.receive_date = timezone.now() - timedelta(hours=5, minutes=0)
    item.save()
    return redirect('/')


def unQuickOrdered(request, id):
    item = ordered.objects.get(pk=id)
    item.order_ordered = False
    item.order_date = timezone.now() - timedelta(hours=5, minutes=0)
    item.save()
    return redirect('/')

def unQuickReceived(request, id):
    item = ordered.objects.get(pk=id)
    item.order_received = False
    item.receive_date = timezone.now() - timedelta(hours=5, minutes=0)
    item.save()
    return redirect('/')




def find_space(spots,usr):
    nfull_shelves = shelf.objects.filter(full=False)
    if spots == 0:
        return None
    num_spots_needed = spots # i.e 4
    for z in nfull_shelves:
        empty_spots = 5 - len(ast.literal_eval(z.occupants)) #i.e. returns 2
        if num_spots_needed <= empty_spots:
                updated_lst = ast.literal_eval(z.occupants)
                updated_lst = updated_lst + [usr]*num_spots_needed
                z.occupants = str(updated_lst)
                if len(ast.literal_eval(z.occupants)) == 5:
                    z.full = True
                z.save()
                break
        else:
            updated_lst = ast.literal_eval(z.occupants)
            updated_lst = updated_lst+[usr]*empty_spots
            z.occupants = str(updated_lst)
            if len(ast.literal_eval(z.occupants)) == 5:
                z.full = True
            z.save()
            num_spots_needed = num_spots_needed - empty_spots
            continue

def get_boxes(request,numneeded):
    usr = request.user.username
    find_space(numneeded,usr)
    return redirect("orderpoll:Box")

def show_my_boxes(user):
    usr = user
    shelves = [z for z in shelf.objects.all() if usr in z.occupants]
    box_dict = {x.name:x.occupants.count(usr) for x in shelves}
    return box_dict

def show_all_boxes():
    shelves = [z for z in shelf.objects.all() if len(ast.literal_eval(z.occupants))>0]
    box_dict = {x.name:x.occupants for x in shelves}
    return box_dict

def del_box(request, shel, usr):
    #useer = request.user.username
    s = shelf.objects.get(name=shel)
    br = ast.literal_eval(s.occupants)
    br.remove(usr)
    s.occupants = br
    if s.full==True:
        s.full=False
    s.save()
    return redirect("/Box")


def logIn(request):
    form_class = loginForm
    form = form_class(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            attempt = form.save(commit=False)
            userName = attempt.username
            userOb = get_object_or_404(Users, username=userName)
            password = userOb.password
            user = authenticate(request, username=userName, password=password)
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                return HttpResponseNotFound('<h1>User not found</h1><br><a href="/login">Try again?</a>')

    return render(request, 'orderpoll/login.html', {'form':form})

def logOut(request):
    logout(request)
    return redirect('/login')

@login_required(login_url='login/')
def newBox(request):
    usr = request.user.username
    boxes = show_my_boxes(usr)
    #del_url = reverse('delete_box', args=[])
    all_boxes = show_all_boxes()
    all_bx_cl = {x:[(z,colors[z]) for z in ast.literal_eval(all_boxes[x])] for x in all_boxes}

    if request.method == "POST":
        form = BoxForm(request.POST)
        if form.is_valid():
            numberNeeded = form.cleaned_data['numberNeeded']
            find_space(numberNeeded,usr)
            return redirect("orderpoll:Box")
    else:
        form = BoxForm()

    return render(request, 'orderpoll/newbox.html',{"myBs":boxes,"form":form, "usr":usr,"allBs":all_boxes, "allcols":all_bx_cl})

@login_required(login_url='login/')
def index(request):
    user = request.user
    managers = [x.fname for x in Users.objects.all() if x.admin == True]


    LJ_over_status = False

    nudge_list = {}

    if request.user.username == 'RP':
        LJReset = LabJob.objects.all()

        for x in LJReset:
            if x.last_completed and x.lifetime and x.status==True and x.last_email:
                if timezone.now().date() >= x.last_completed+timedelta(days=round(x.lifetime*0.8)) and x.last_email != timezone.now().date():
                    x.status = False
                    x.nudge = x.nudge+1
                    #x.last_email = timezone.now().date()
                    x.save()

            if x.last_completed and x.lifetime and x.status==False and x.last_email:
                if timezone.now().date() == x.last_completed+timedelta(days=round(x.lifetime))+timedelta(days=0) and x.last_email != timezone.now().date() and x.user.username != 'JS':
                    print(x.job+'is due')#+timedelta(days=2))
                    x.last_email = timezone.now().date()

                    x.save()
                    #ezgmail.send(str(emaildict.get(x.user.username)),"[Reminder][Lab Jobs] "+x.job+" ", "Please complete this in a timely manner. Your labmates will appreciate it. Thanks!")
                if timezone.now().date() == x.last_completed+timedelta(days=round(x.lifetime))+timedelta(days=7) and x.last_email != timezone.now().date() and x.user.username != 'JS':
                    x.last_email = timezone.now().date()
                    x.save()
                    #ezgmail.send(str(emaildict.get(x.user.username)),"[Reminder][Lab Jobs] "+x.job+" ", "Please complete this in a timely manner. Your labmates will appreciate it. Thanks!")

    if request.method == "POST":
        LabJobFset = LabJobFormset(request.POST, queryset=LabJob.objects.filter(user=Users.objects.get(User=request.user)))

        for field in LabJobFset:
            print("Field Error:", field.errors)
        #print(LabJobFset)#, queryset=LabJob.objects.filter(user=Users.objects.get(User=request.user)))
        if LabJobFset.is_valid():
            change_list = []
            for y,x in enumerate(LabJobFset):
                if 'status' in x.changed_data:
                    change_list.append(y)
            print(change_list)
            data = LabJobFset.save(commit=False)
            for y,x in enumerate(data):
                if y in change_list and x.status is True:
                    if x.last_completed and x.lifetime:
                        print('check')
                        diff = (timezone.now().date() - x.last_completed).days - x.lifetime
                        if diff <= 0:
                            x.score = x.score+1
                        elif diff > 0:
                            x.score = x.score-1
                    else:
                        print('fail')
                        pass
                    x.nudge=0
                    x.last_completed= timezone.now() - timedelta(hours=5, minutes=0)

                x.save()

        #else:
            #print('Invalid')
        return redirect('/')
    else:
        LabJobFset = LabJobFormset(queryset=LabJob.objects.filter(user=Users.objects.get(User=request.user)))
        for y, x in enumerate(LabJob.objects.filter(user=Users.objects.get(User=request.user))):
            nudge_list[y] = x.nudge
    print(nudge_list)
    #print(list(nudge_list.values())[0])


    latest_inventory_list = inventory.objects.all()
    ordered_list = [x for x in ordered.objects.filter(order_suggest=False).order_by('-request_date')][:40]
    #order_list = ordered.objects.filter(order_ordered =True).filter(order_received=False).order_by('-request_date')[:30]
    context = {"nudge_list":list(nudge_list.values()),"LJFset":LabJobFset,'latest_inventory_list':latest_inventory_list, 'ordered':ordered_list, 'user':user, 'managers':managers}
    #"LJ_over_status":LJ_over_status,'labjobform':labjobform,
    return render(request, 'orderpoll/index.html',context)

def NudgePage(request):
    user = request.user

    if request.method == 'POST':
        LabJobFsetNudge = LabJobFormsetNudge(request.POST, queryset=LabJob.objects.all())
    else:
        LabJobFsetNudge = LabJobFormsetNudge(queryset=LabJob.objects.all())

    return render(request, 'orderpoll/nudge.html', {'Fset':LabJobFsetNudge})

def nudged(request, pk1):
    user = request.user
    job = get_object_or_404(LabJob, pk=pk1)


    job.nudge = job.nudge+1
    job.status = False
    if job.nudge == 1:
        ezgmail.send(str(emaildict.get(job.user.username)),"[Lab Jobs] Someone requested completion of "+job.job+" ", "Please complete this in a timely manner. Your labmates will appreciate it. Thanks! -Hannan")
    elif job.nudge == 5:
        ezgmail.send(str(emaildict.get(job.user.username)),"[Reminder][Lab Jobs] Someone requested completion of "+job.job+" ", "Please complete this in a timely manner. Your labmates will appreciate it. Thanks! -Hannan")
    elif job.nudge == 10:
        ezgmail.send(str(emaildict.get('ahm421')),"[Reminder][Lab Jobs] Someone requested completion of "+job.job+" ", "This lab job has not been completed. Please speak with the person responsible.")

    job.save()
    return redirect('/nudge/')


@login_required(login_url='login/')
def order_note(request, pk):
    note = get_object_or_404(ordered, pk=pk)
    return render(request, 'orderpoll/notes.html', {'object':note})


@login_required(login_url='login/')
def labmanPanel(request):
    ordered_list = ordered.objects.order_by('request_date')
    user = request.user
    orderpks = []
    for x in range(0, len(ordered_list)):
        orderpks.append(ordered_list.values()[x]['id'])

    if request.method == 'POST':
        formset = OrderReceiveFormset(request.POST, request.FILES, queryset=ordered.objects.filter(order_suggest=False).filter(order_received=False).order_by('-request_date'))
        if formset.is_valid():
            receive = formset.save()
            for x in receive:
                if x.order_email is True:
                    if x.order_ordered is True:
                        ezgmail.send(str(emaildict.get(x.order_owner)),"[Ordering] "+x.order_description+" was ordered!", "I'll keep you updated about "+x.order_description+". Thanks! -Hannan")
                    if x.order_received is True:
                        ezgmail.send(str(emaildict.get(x.order_owner)),"[Ordering] "+x.order_description+" was received!", "I'll keep "+x.order_description+" at my bay for now. Please come to collect it. Thanks! -Hannan")
            return redirect('/')
    else:
        formset = OrderReceiveFormset(queryset=ordered.objects.filter(order_suggest=False).filter(order_received=False).order_by('-request_date'))
    return render(request, 'orderpoll/manage_orders.html', {'formset':formset})

@login_required(login_url='login/')
def editOrder(request, pk):
    user = request.user
    latest_inventory_list = inventory.objects.all()
    post = get_object_or_404(ordered, pk=pk)
    if request.method =='POST':
        form = OrderForm(request.POST, instance=post)
        if form.is_valid():
            order = form.save(commit=False)
            order.order_description = inventory.objects.filter(item_code=order.order_code).values()[0]['item_description']
            order.order_category = inventory.objects.filter(item_code=order.order_code).values()[0]['item_category']
            order.order_owner = str(user.username)
            order.request_date = timezone.now() - timedelta(hours=5, minutes=0)
            order.save()
            if order.order_email is True:
                    ezgmail.send(str(emaildict.get(order.order_owner)),'[Ordering] New Item Requested', 'You asked to receive emails about the following requested item: '+order.order_description+". Thanks! We'll keep you updated!")
            return redirect('/')
    else:
        form = OrderForm(instance=post)
    return render(request, 'orderpoll/editOrder.html', {'form':form, 'latest_inventory_list':latest_inventory_list})

@login_required(login_url='login/')
def delOrder(request, pk):
    post = get_object_or_404(ordered, pk=pk)
    del_code = post.order_code
    
    post.delete()
    def stat_checker(order_code1):
        order_codes = [x for x in ordered.objects.filter(order_code=order_code1)]
        if len(order_codes)>1:
            dates = list(map(lambda z: z['request_date'], ordered.objects.filter(order_code=order_code1).values()))
            deltas = np.diff(dates)
            datesOrderArriv = [(z['receive_date'],z['order_date']) for z in ordered.objects.filter(order_code=order_code1).values() if z['receive_date'] is not None and z['order_date'] is not None]
            deltasOrderArriv = [(i-q) for i,q in datesOrderArriv]
            return str(np.median(deltas))
        else:
            return "Nothing yet"
    try:
        q = inventory.objects.get(item_code=del_code)
        print('success deletion')
        q.item_stats = str(stat_checker(del_code))
        q.save()
    except:
        pass
    return render(request, 'orderpoll/deleteOrder.html', {'post':post})

@login_required(login_url='login/')
def getOrder(request):
    user = request.user
    admins = [x.username for x in Users.objects.all() if x.admin == True]
    latest_inventory_list = inventory.objects.all()
    recent_codes = {}
    recent_orders = ordered.objects.filter(order_received=False).values()
    frequent_orders = ['NI NF300',]
    for x in recent_orders:
        recent_codes.update({x['order_code']:x['request_date']})
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.order_description = inventory.objects.filter(item_code=order.order_code).values()[0]['item_description']
            order.order_category = inventory.objects.filter(item_code=order.order_code).values()[0]['item_category']
            order.order_owner = user.username
            order.request_date = timezone.now() - timedelta(hours=5, minutes=0)
            order.inven_item = inventory.objects.filter(item_code = order.order_code).order_by('-post_date')[0]
            order.save()
            if order.order_email is True:
                ezgmail.send(str(emaildict.get(order.order_owner)),'[Ordering] '+order.order_description+' Requested', 'You asked to receive emails about the following requested item: '+order.order_description+". Thanks! We'll keep you updated!")


            def stat_checker(order_code1):
                order_codes = [x for x in ordered.objects.filter(order_code=order_code1)]
                if len(order_codes)>1:
                    dates = list(map(lambda z: z['request_date'], ordered.objects.filter(order_code=order_code1).values()))
                    deltas = np.diff(dates)
                    datesOrderArriv = [(z['receive_date'],z['order_date']) for z in ordered.objects.filter(order_code=order_code1).values() if z['receive_date'] is not None and z['order_date'] is not None]
                    deltasOrderArriv = [(i-q) for i,q in datesOrderArriv]
                    return str(np.median(deltas))
                else:
                    return "Nothing yet"
            try:
                q = inventory.objects.get(item_code=order.order_code)
                q.item_stats = str(stat_checker(order.order_code))
                q.save()
            except:
                ezgmail.send(str(emaildict.get('ahm421')),'[Ordering] '+order.order_description+' ',order.order_code+' Duplicate created!')

            return redirect('/')
    else:
        form = OrderForm()
    return render(request, 'orderpoll/getOrder.html', {'form':form, 'latest_inventory_list':latest_inventory_list})


@login_required(login_url='login/')
def newItem(request):
    user = request.user
    managers = [x.fname for x in Users.objects.all() if x.admin == True]
    admins = [x.username for x in Users.objects.all() if x.admin == True]

    def other2orderinven(id):
        y = Other.objects.get(pk=id)
        q = ordered(order_description = y.other_description, order_code = y.other_code, order_category = y.other_category, order_quantity = y.other_quantity, order_units=y.other_units, order_owner = user.username, order_notes = y.other_notes, order_email=y.other_email ,request_date = y.post_date)
        if q.order_owner in admins:
            q.order_date = timezone.now() - timedelta(hours=5, minutes=0)
            q.order_ordered = True
            q.save()
        else:
            q.save()
        if q.order_email is True:
            ezgmail.send(str(emaildict.get(q.order_owner)),'[Ordering] New Item Requested: '+q.order_description,'You asked to receive emails about the following requested item: '+q.order_description+". Thanks! We'll keep you updated!")
        p = inventory(item_description = y.other_description, item_code = y.other_code, item_manufacturer=y.other_manufacturer, item_category=y.other_category, item_link=y.other_link, item_quick=False, post_date = y.post_date)
        p.save()



    def alreadyexistsininven(id):
        if Other.objects.get(pk=id).other_code in current_inven:
            return True

    if request.method == 'POST':
        form = newItemForm(request.POST)
        if form.is_valid():
            newItem = form.save(commit=False)
            newItem.post_date = timezone.now() - timedelta(hours=5, minutes=0)
            newItem.save()
            Other1 = Other.objects.all()
            Otherkeys = list(map(lambda n:n.id, Other1))
            facts = []
            for x in Otherkeys:
                if Other.objects.get(pk=x).other_code not in current_inven:
                    other2orderinven(x)
                else:
                    facts.append(alreadyexistsininven(x))
                Other.objects.get(pk=x).delete()


        return HttpResponse('<h1>Item already exists in inventory! </h1><br><a href="/">Go Home</a>') if len(facts)>0 else redirect('/')
    else:
        form = newItemForm()



    formset = BulkNewItemFormset(request.POST or None)
    if request.method == 'POST':
        if formset.is_valid():
            newitems = formset.save()
            Otherkeys = []
            for x in Other.objects.values():
                Otherkeys.append(x['id'])
            for x in Otherkeys:
                   y = Other.objects.get(pk=x)
                   q = ordered(order_description = y.other_description, order_code = y.other_code, order_category = y.other_category, order_quantity = y.other_quantity,order_units=y.other_units, order_owner = user, order_notes = y.other_notes, request_date = y.post_date)
                   q.save()
                   p = inventory(item_description = y.other_description, item_code = y.other_code, item_manufacturer=y.other_manufacturer, item_category=y.other_category, item_link=y.other_link, item_quick=False, post_date = y.post_date)
                   p.save()
            return redirect('/')
        else:
            form = newItemForm()

    return render(request, 'orderpoll/newItem.html', {'form':form, 'formset':formset,'managers':managers})

@login_required(login_url='login/')
def orderHistory(request):
    order_list = ordered.objects.filter(order_suggest=False).order_by('-request_date')
    user = request.user
    managers = [x.fname for x in Users.objects.all() if x.admin == True]
    return render(request, 'orderpoll/history.html', {'order_list':order_list,'user':user, 'managers':managers})

@login_required(login_url='login/')
def inventoryPage(request):
    order_codes=list(map(lambda x: x.order_code, ordered.objects.all()))
    user = request.user
    managers = [x.fname for x in Users.objects.all() if x.admin == True]
    def stat_checker(order_code):
        if order_codes.count(order_code)>1:
            dates = list(map(lambda z: z['request_date'], ordered.objects.filter(order_code=order_code).values()))
            deltas = np.diff(dates)
            datesOrderArriv = [(z['receive_date'],z['order_date']) for z in ordered.objects.filter(order_code=order_code).values() if z['receive_date'] is not None and z['order_date'] is not None]
            deltasOrderArriv = [(i-q) for i,q in datesOrderArriv]
            return str(np.median(deltas))
        else:
            return "Nothing yet"
    #for x in order_codes:
    #    q = inventory.objects.get(item_code=x)
    #    q.item_stats = str(stat_checker(x))
    #    q.save()
    inventory1 = inventory.objects.order_by('-item_category')
    return render(request, 'orderpoll/inventory.html',{'inventory':inventory1,'user':user, 'managers':managers})

@login_required(login_url='login/')
def OrderHelper(request):
    order_codes = [x.order_code for x in ordered.objects.all()]
    user = request.user
    managers = [x.fname for x in Users.objects.all() if x.admin == True]
    ##############################################
    current_suggested = [x.order_description for x in ordered.objects.filter(order_suggest=True)]
    helper = [x for x in inventory.objects.all() if x.item_stats != "Nothing yet" and len(ordered.objects.filter(order_code=x.item_code))>2 and x.item_description not in current_suggested and x.item_category != 'Antibody' and x.item_category != 'Nitrogen Tanks']

    today = pytz.utc.localize(datetime.today())

    for x in helper:

        last_order = ordered.objects.filter(order_code = x.item_code).order_by('-request_date')[0].request_date
        print(x.item_stats)
        print(x.item_code)
        print(x.item_description)

        next_order = last_order + timedelta(seconds=timeparse(x.item_stats))
        print(x.item_code)
        print(next_order)
        print(" ")

        if next_order > today:
            pass
        elif next_order <= today:
            newOrder = ordered(order_description = x.item_description, order_code = x.item_code, order_category = x.item_category, order_quantity = 1,order_units='EA', order_owner = user, order_notes = '', request_date = today, order_suggest=True)
            newOrder.save()

    suggested_orders = ordered.objects.filter(order_suggest=True)

    context = {"suggested_orders":suggested_orders, 'user':user, 'managers':managers}
    return render(request, 'orderpoll/suggestions.html', context)

@login_required(login_url='login/')
def snooze(request, pk1, order_code, days):
    snoozer = get_object_or_404(inventory, item_code=order_code)
    snoozer.item_stats = str(timedelta(seconds=timeparse(snoozer.item_stats))+timedelta(seconds=(86400*int(days))))
    snoozer.save()
    suggestion = get_object_or_404(ordered, pk=pk1)#ordered.objects.filter(order_code = order_code).filter(order_suggest=True).order_by('-order_date')[0]
    suggestion.delete()

    return redirect('/suggestions/')

@login_required(login_url='login/')
def accept_suggest(request, pk):
    today = pytz.utc.localize(datetime.today())
    acceptor = get_object_or_404(ordered, pk=pk)
    acceptor.order_suggest = False
    acceptor.request_date = today
    codecode = acceptor.order_code
    acceptor.save()

    def stat_checker(order_code1):
        order_codes = [x for x in ordered.objects.filter(order_code=order_code1)]
        print([x.request_date for x in order_codes])
        if len(order_codes)>1:
            dates = list(map(lambda z: z['request_date'], ordered.objects.filter(order_code=order_code1).values()))
            deltas = np.diff(dates)
            datesOrderArriv = [(z['receive_date'],z['order_date']) for z in ordered.objects.filter(order_code=order_code1).values() if z['receive_date'] is not None and z['order_date'] is not None]
            deltasOrderArriv = [(i-q) for i,q in datesOrderArriv]
            return str(np.median(deltas))
        else:
            return "Nothing yet"
    try:
        orderthis = ordered.objects.get(pk=acceptor.pk)
        q = inventory.objects.get(item_code=codecode)
        q.item_stats = str(stat_checker(codecode))
        q.save()
        print('success acceptance')

    except:
        print('order not available yet')
        ezgmail.send(str(emaildict.get('ahm421')),'[Ordering] '+acceptor.order_description+' ', acceptor.order_code+' Error in accepting!')

    return redirect ('/suggestions/')

@login_required(login_url='login/')
def editInven(request, pk):
    user = request.user
    post = get_object_or_404(inventory, pk=pk)
    latest_inventory_list = inventory.objects.all()
    if request.method =='POST':
        form = InvenEditForm(request.POST, instance=post)
        if form.is_valid():
            inven = form.save()
            return redirect('/inventoryPage/')
    else:
        form = InvenEditForm(instance=post)
    return render(request, 'orderpoll/editInventory.html', {'form':form, 'latest_inventory_list':latest_inventory_list})

@login_required(login_url='login/')
def pagePO(request):
    user = request.user
    PO1s = POs.objects.order_by('-date_added')
    return render(request, 'orderpoll/POs.html', {'POs':PO1s})
