import random
from django.http import HttpResponse
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from meiduo_mull.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from meiduo_mull.apps.varifications import constants
import logging
from .serializers import ImageCodeCheckSerializer
from meiduo_mull.utils.yuntongxun.sms import CCP
from rest_framework import status
from celery_tasks.sms.tasks import send_sms_code
# Create your views here.
logger = logging .getLogger('django')


class ImageCodeView(APIView):
    """图片验证码"""
    def get(self, request, image_code_id):

        # 生成图形验证码
        text, image = captcha.generate_captcha()
        # 保存真实值
        # 连接要保存到的数据库redis
        redis_conn = get_redis_connection('verify_codes')
        # 保存并设置过期时间
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        #  返回图片
        # print(text)
        # print(image_code_id)
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(GenericAPIView):
    """
    短信验证码
    text, image_code_id, 手机号mobile

    """
    # 指定序列化器
    serializer_class = ImageCodeCheckSerializer

    def get(self,request, mobile):
        # 检验参数, 由序列化器完成
        serializers = self.get_serializer(data=request.query_params)
        serializers.is_valid(raise_exception=True)
        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)
        # 保存短信验证码　，发送记录
        redis_conn = get_redis_connection('verify_codes')
        # 使用管道
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES,sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # 执行管道
        pl.execute()
        # 发送短信，　
        # try:
        #     ccp = CCP()
        #     expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        #     result = ccp.send_template_sms(mobile, [sms_code,expires], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error("发送验证码短信[异常][ mobile: %s, message: %s ]" % (mobile, e))
        #     return Response({'message': 'OK'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # else:
        #     if result == 0:
        #         logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        #         return Response({'message': 'OK'})
        #     else:
        #         logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)
        #         return Response({'message': 'OK'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #使用celer发送异步任务
        expires = constants.SMS_CODE_REDIS_EXPIRES // 60
        temp_id = constants.SMS_CODE_TEMP_ID
        send_sms_code(expires, mobile,sms_code,temp_id)
        return Response({'message': 'OK'})