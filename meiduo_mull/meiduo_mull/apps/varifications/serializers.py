from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from django_redis import get_redis_connection


class ImageCodeCheckSerializer(serializers.Serializer):
    """
    图片验证码序列化器
    image_code_id, text
    """
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4, min_length=4)

    def validate(self, attrs):
        # 检验参数
        image_code_id = attrs['image_code_id']
        text = attrs['text']
        # 查询真实图片验证码
        redis_conn = get_redis_connection('verify_codes')
        redis_image_code_text = redis_conn.get('img_%s' % image_code_id)
        # 判断是否存在
        if not redis_image_code_text:
            raise serializers.ValidationError('图片验证码无效')
        # 删除redis中的图片验证码
        redis_conn.delete('img_%s' % image_code_id)
        # 比较图片验证码
        redis_image_code_text = redis_image_code_text.decode()
        if redis_image_code_text.lower() != text.lower():
            raise serializers.ValidationError('图片验证码错误')
        # 判断是否在６０秒内
        mobile = self.context['view'].kwargs['mobile']
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            raise serializers.ValidationError('请求次数过于频繁')
        return attrs