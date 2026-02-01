from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import AccessCard, VolunteerAccount
import json
import datetime
import random
import string

def login_view(request):
    if request.method == "POST":
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('/dashboard/')
        else:
            return render(request, 'card_auth/login.html', {'error': '用户名或密码错误'})
    return render(request, 'card_auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required(login_url='/login/')
def dashboard(request):
    """
    Intelligent Dashboard Router
    - Superusers -> Admin Dashboard
    - Normal Users (Students) -> User Dashboard
    """
    if request.user.is_superuser:
        return render(request, 'card_auth/dashboard.html')
    
    # Check if user has a card linked
    try:
        card = request.user.card
        return render(request, 'card_auth/user_dashboard.html', {'card': card})
    except AccessCard.DoesNotExist:
        return render(request, 'card_auth/login.html', {'error': '此账号未绑定任何卡密'})

# --- Public API for Extension (CSRF Exempt) ---

@csrf_exempt
def get_credentials(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
        card_key = data.get("card_key")
        device_id = data.get("device_id") # New param

        if not card_key: return JsonResponse({"success": False, "error": "Missing card_key"}, status=400)
        if not device_id: return JsonResponse({"success": False, "error": "请升级插件 (Missing device_id)"}, status=400)
        
        try:
            card = AccessCard.objects.get(code=card_key)
        except AccessCard.DoesNotExist:
            return JsonResponse({"success": False, "error": "无效的卡密"}, status=404)

        # check validity
        if not card.is_valid():
             return JsonResponse({"success": False, "error": "卡密已过期"}, status=403)

        # --- Security: Device Binding ---
        if not card.bound_device_id:
            # First use: Bind it!
            card.bound_device_id = device_id
            card.save()
        elif card.bound_device_id != device_id:
            # Mismatch: Block it!
            return JsonResponse({"success": False, "error": "安全警告：此卡密已绑定其他设备，无法在此电脑使用。"}, status=403)
        # --------------------------------

        account = card.linked_account
        return JsonResponse({
            "success": True,
            "username": account.platform_username,
            "password": account.platform_password,
            "account_name": account.name
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# --- Admin Management APIs ---

def dashboard_data(request):
    if not request.user.is_superuser: return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    accounts = list(VolunteerAccount.objects.values('id', 'name', 'platform_username').order_by('-id'))
    cards = []
    for c in AccessCard.objects.all().order_by('-created_at'):
        expiry_str = c.expiry_time.strftime("%Y-%m-%d %H:%M") if c.expiry_time else "永久"
        cards.append({
            'id': c.id,
            'code': c.code,
            'account_name': c.linked_account.name,
            'expiry': expiry_str,
            'auto_renew': c.auto_renew,
            'student_user': c.user.username if c.user else None,
            'is_bound': bool(c.bound_device_id) # Send binding status
        })
        
    return JsonResponse({'accounts': accounts, 'cards': cards})

@csrf_exempt
def unbind_card(request):
    """Admin can reset the binding"""
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            card = AccessCard.objects.get(id=data['id'])
            card.bound_device_id = None # Clear it
            card.save()
            return JsonResponse({'status': 'ok'})
        except Exception:
            return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def add_account(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        VolunteerAccount.objects.create(
            name=data['name'],
            platform_username=data['username'],
            platform_password=data['password']
        )
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def generate_card(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        account = VolunteerAccount.objects.get(id=data['account_id'])
        duration = int(data['duration_hours'])
        auto_renew = data.get('auto_renew', False)
        
        # Student Login Info
        s_user = data.get('student_user')
        s_pass = data.get('student_pass')
        
        code = ''.join(random.choices(string.digits, k=6))
        while AccessCard.objects.filter(code=code).exists():
             code = ''.join(random.choices(string.digits, k=6))

        expiry = timezone.now() + datetime.timedelta(hours=duration)
        
        card = AccessCard(
            code=code,
            linked_account=account,
            expiry_time=expiry,
            auto_renew=auto_renew
        )
        
        # Create User if provided
        if s_user and s_pass:
            if User.objects.filter(username=s_user).exists():
                return JsonResponse({'status': 'error', 'message': '用户名已存在'}, status=400)
            user = User.objects.create_user(username=s_user, password=s_pass)
            card.user = user
            
        card.save()
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def toggle_renew(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            card = AccessCard.objects.get(id=data['id'])
            card.auto_renew = data['auto_renew']
            card.save()
            return JsonResponse({'status': 'ok'})
        except Exception:
            return JsonResponse({'status': 'error'}, status=400)

@csrf_exempt
def delete_account(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        VolunteerAccount.objects.filter(id=data['id']).delete()
        return JsonResponse({'status': 'ok'})

@csrf_exempt
def delete_card(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        card = AccessCard.objects.get(id=data['id'])
        # Also delete the associated user if it exists
        if card.user:
            card.user.delete()
        card.delete()
        return JsonResponse({'status': 'ok'})
