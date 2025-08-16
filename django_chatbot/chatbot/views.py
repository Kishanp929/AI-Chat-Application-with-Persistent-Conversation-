from django.shortcuts import render , redirect
from django.http import JsonResponse
from django.contrib.auth.models import User 
import requests
from django.contrib import auth 
from .models import Chat
from django.utils import timezone
import os
import markdown2
from django.contrib.auth.decorators import login_required


# Securely load Gemini API key from environment variable
GEMINI_API_KEY = "AIzaSyB_pE9WrTYpJErEEKLrN5zq6AbpwfAgVes"




def format_response(raw_text):
    html = markdown2.markdown(
        raw_text,
        extras=['fenced-code-blocks', 'code-friendly', 'break-on-newline', 'mathjax']
    )
    return html


def ask_gemini_api(message):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    data = {
        "contents": [
            {
                "parts": [
                    {"text": message}
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    print("Status Code:", response.status_code)
    print(response)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": f"Request failed with status {response.status_code}: {response.text}"
        }


def chatbot(request):
   
    if not request.user.is_authenticated:
        if request.method == 'POST':
            message = request.POST.get('message')

            gemini_response = ask_gemini_api( message )
        
            # Extract the response text safely
            text_response = ""
            if 'error' in gemini_response:
                text_response = format_response( gemini_response['error'] )
            else:
                try:
                    text_response = format_response( gemini_response['candidates'][0]['content']['parts'][0]['text'] )
                except (KeyError, IndexError, TypeError):
                    text_response = "Sorry, I couldn't understand that."

            
            return JsonResponse({
                'status': 'success',
                'message': message,
                'response': text_response
            })
        return render(request, 'chatbot.html')

        
    chats = Chat.objects.filter( user = request.user   )
    if request.method == 'POST':
        message = request.POST.get('message')

        gemini_response = ask_gemini_api( message )
       
        # Extract the response text safely
        text_response = ""
        if 'error' in gemini_response:
            text_response = format_response( gemini_response['error'] )
        else:
            try:
                text_response = format_response( gemini_response['candidates'][0]['content']['parts'][0]['text'] )
            except (KeyError, IndexError, TypeError):
                text_response = "Sorry, I couldn't understand that."

        chat = Chat(user = request.user , message=message , response = text_response , created_at = timezone.now())
        chat.save()
        return JsonResponse({
            'status': 'success',
            'message': message,
            'response': text_response
        })

    return render(request, 'chatbot.html' , { 'chats' : chats })


def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None :
            auth.login(request, user)
            return redirect('chatbot')
        else:
            return render(request, 'login.html', {'error_message': 'Invalid username or password.'})
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email' )
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if password1 == password2:
       
            try:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                auth.login(request , user )
         
                return redirect('chatbot')
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                
                return render(request, 'register.html', {'error_message': error_message})
        else:
     
            errot_message = "Passwords do not match."
            return render(request, 'register.html', {'error_message': errot_message})
    
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')