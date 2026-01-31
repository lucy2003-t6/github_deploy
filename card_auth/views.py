from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import AccessCard, VolunteerAccount
import json
import datetime
import random
import string

def dashboard(request):
    """Render the simple management page"""
    return render(request, 'card_auth/dashboard.html')

@csrf_exempt
def get_credentials(request):
    """Existing API for extension"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
        card_key = data.get("card_key")
        if not card_key: return JsonResponse({"success": False, "error": "Missing card_key"}, status=400)
        
        try:
            card = AccessCard.objects.get(code=card_key)
        except AccessCard.DoesNotExist:
            return JsonResponse({"success": False, "error": "无效的卡密"}, status=404)

        if not card.is_valid():
             return JsonResponse({"success": False, "error": "卡密已过期或被禁用"}, status=403)

        account = card.linked_account
        return JsonResponse({
            "success": True,
            "username": account.platform_username,
            "password": account.platform_password,
            "account_name": account.name
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# --- Management APIs ---

def dashboard_data(request):
    accounts = list(VolunteerAccount.objects.values('id', 'name', 'platform_username').order_by('-id'))
    cards = []
    for c in AccessCard.objects.filter(is_active=True).order_by('-created_at'):
        expiry_str = c.expiry_time.strftime("%Y-%m-%d %H:%M") if c.expiry_time else "永久"
        cards.append({
            'id': c.id,
            'code': c.code,
            'account_name': c.linked_account.name,
            'expiry': expiry_str
        })
        
    return JsonResponse({'accounts': accounts, 'cards': cards})

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
        
        # Generate simple 6-digit number or random string
        # User asked for 'random generation'
        code = ''.join(random.choices(string.digits, k=6))
        
        # Avoid duplicate
        while AccessCard.objects.filter(code=code).exists():
             code = ''.join(random.choices(string.digits, k=6))

        expiry = timezone.now() + datetime.timedelta(hours=duration)
        
        AccessCard.objects.create(
            code=code,
            linked_account=account,
            expiry_time=expiry
        )
        return JsonResponse({'status': 'ok'})

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
        AccessCard.objects.filter(id=data['id']).delete()
        return JsonResponse({'status': 'ok'})
