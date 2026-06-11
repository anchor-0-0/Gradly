import uuid
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from ..serializers import RegisterSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from ..models import PasswordResetCode
from django.contrib.auth.models import User


# تسجيل حساب جديد (للطلاب)
# POST /api/register/
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# تسجيل الدخول (لجميع المستخدمين)
# POST /api/login/
# يعيد token + is_staff + is_superuser
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            })
        return Response(
            {'error': 'بيانات الدخول غير صحيحة'},
            status=status.HTTP_400_BAD_REQUEST
        )


# -- إرسال رمز إعادة تعيين كلمة المرور (نسيت كلمة المرور) --
# POST /api/forgot-password/
# يتحقق من وجود الإيميل، ينشئ رمز UUID فريد، ويخزنه في جدول PasswordResetCode
# ملاحظة: في الإنتاج يتم إرسال الرمز عبر البريد الإلكتروني، هنا نرجعه في الاستجابة للتطوير
class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        # إنشاء رمز فريد لإعادة التعيين
        code = str(uuid.uuid4())
        PasswordResetCode.objects.create(email=email, code=code)

        return Response({
            'message': 'تم إرسال رمز إعادة تعيين كلمة المرور إلى بريدك الإلكتروني',
            'code': code,  # يرجع الرمز في التطوير فقط; في الإنتاج يُرسل عبر email
        })


# -- إعادة تعيين كلمة المرور باستخدام الرمز --
# POST /api/reset-password/
# يتحقق من صحة الرمز (غير منتهي الصلاحية ولم يُستخدم بعد)، ثم يعيّن كلمة المرور الجديدة
class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        # جلب رمز التحقق والتأكد من صلاحيته (لم يمضِ عليه أكثر من ساعة)
        reset_code = PasswordResetCode.objects.get(
            email=email, code=code, is_used=False
        )
        if reset_code.created_at < timezone.now() - timedelta(hours=1):
            return Response({'error': 'انتهت صلاحية الرمز، يرجى طلب رمز جديد'},
                            status=status.HTTP_400_BAD_REQUEST)

        # تغيير كلمة المرور
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'المستخدم غير موجود'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        # تعليم الرمز كمستخدم
        reset_code.is_used = True
        reset_code.save()

        return Response({'message': 'تم إعادة تعيين كلمة المرور بنجاح'})
