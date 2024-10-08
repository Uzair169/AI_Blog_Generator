from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
import openai
import yt_dlp
import requests
import httpx 


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html') 

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
            # return JsonResponse({'content': yt_link})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)
        
        # get yt link 
        title = yt_title(yt_link)

        # get transcript 
        transcription = get_transcrption(yt_link)
        if not transcription:
            return JsonResponse({'error': " Failed to get transcript"}, status=500)
        
        # Use openAI to generate the blog 
        
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': " Failed to generate blog article"}, status=500)
        
        # save blog article to database

        # return blog article as a response 
        return JsonResponse({'content': blog_content})


    else:
        return JsonResponse({'error': 'Invalid request method'}, status= 405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    # yt = YouTube(link)
    # video = yt.streams.filter(only_audio=True).first()
    # out_file = video.download(output_path=settings.MEDIA_ROOT)
    # base, ext = os.path.splitext(out_file)
    # new_file = base + '.mp3'
    # os.rename(out_file, new_file)
    # return new_file
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'ffmpeg_location': '/usr/bin/ffmpeg', 
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    return 'audio.mp3'


def get_transcrption(link):
    audio_file = download_audio(link)
    aai.settings.api_key = "67a937186b55489ea297a21f2dca423d"
    # try:
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text
    # except:
        # return JsonResponse({'error': 'The upload operation timed out, please increase the timeout'}, status= 405)
    # return transcript.text  


def generate_blog_from_transcription(transcription):


    # prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but don't make it look like a youtube video, make it look like a proper blog: \n\n{transcription}\n\n Article:"

    # response = openai.Completion.create(
    #     model="gpt-3.5-turbo-instruct",
    #     prompt=prompt,
    #     max_tokens=1000 
    # )

    # generated_content = response.choices[0].text.strip()

    # return generated_content

    api_key = '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'  # Replace with your Hugging Face API key

    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but don't make it look like a YouTube video, make it look like a proper blog: \n\n{transcription}\n\n Article:"

    response = requests.post(
        'https://api-inference.huggingface.co/models/gpt2',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'inputs': prompt, 'parameters': {'max_length': 1000}}
    )

    # generated_content = response.json()[0]['generated_text'].strip()

    # return generated_content

    try:
        # Check the response structure
        response_json = response.json()
        print("API Response:", response_json)

        if isinstance(response_json, list) and len(response_json) > 0 and 'generated_text' in response_json[0]:
            generated_content = response_json[0]['generated_text'].strip()
        else:
            # Handle unexpected response format
            return "Error: Unexpected response format from the API."

    except Exception as e:
        # Handle any other exceptions that may occur
        return f"Error: {str(e)}"

    return generated_content


def user_login(request):
     if request.method == 'POST':
         username = request.POST['username']
         password = request.POST['password']

         user = authenticate(request, username=username, password=password)
         if user is not None:
            login(request, user)
            return redirect('/')
         else:
            error_message = "Invalid Username or Password"
            return render(request, 'login.html', {'error_message':error_message})
            
     return render(request, 'login.html')

def user_signup(request):
    # print(request)
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except IntegrityError as e:
                print("Integrity Error:", e)
                error_message = 'Username or email already exists.'
            except Exception as e:
                print("General Error:", e)
                error_message = f'Error creating account: {e}'
            # except:
            #     error_message = 'Error creating account'
            return render(request, 'signup.html', {'error_message':error_message})

        else:
            error_message = 'Passwords do not match'
            return render(request, 'signup.html', {'error_message':error_message})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')

