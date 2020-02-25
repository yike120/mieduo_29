from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
# Create your views here.
from meiduo_mull.apps.users.models import User


class UsernameCountView(APIView):
    """判断用户是否存在　数量"""
    def get(self,request, username):
        count = User.objects.filter(username=username).count()
        data = {
            'username': username,
            'count': count
        }
        return Response(data)


class MobileCountView(APIView):
    """判断手机号是否存在"""
    def get(self,request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        data = {
            'mobile':mobile,
            'count': count
        }
        return Response(data)