from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .serializers import (
    UserSerializer, UserCreateSerializer,
    PasswordChangeSerializer, ProfileSerializer
)
from apps.loans.models import BookLoan
from apps.fines.models import Fine

User = get_user_model()

# API ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['register', 'login']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Please provide both username and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class ProfileViewSet(viewsets.ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(id=self.request.user.id)

    def get_object(self):
        if self.action in ['retrieve', 'me']:
            return self.request.user
        return super().get_object()

# Web Views
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Specify the authentication backend to use
            from django.contrib.auth import get_backends
            backend = 'django.contrib.auth.backends.ModelBackend'
            user.backend = backend
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard:dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect(request.GET.get('next', 'dashboard:index'))
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:profile')
    else:
        form = SetPasswordForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})

def password_reset_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                # Generate reset token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Build reset URL
                reset_url = request.build_absolute_uri(
                    reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )
                
                # Create email content
                context = {
                    'user': user,
                    'reset_url': reset_url,
                    'site_name': 'Library Management System',
                }
                email_subject = 'Reset your password'
                email_body = render_to_string('accounts/emails/password_reset_email.html', context)
                
                # Send email
                send_mail(
                    email_subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            
            messages.success(request, 'If an account exists with the email provided, you will receive password reset instructions.')
            return redirect('accounts:login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})

def password_reset_confirm_view(request, uidb64, token):
    try:
        # Decode the user id
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Check if the token is valid
    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('accounts:login')
        else:
            form = SetPasswordForm(user)
    else:
        validlink = False
        form = None
    
    return render(request, 'accounts/password_reset_confirm.html', {
        'form': form,
        'validlink': validlink
    })

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    # Get user's loan statistics
    active_loans = BookLoan.objects.filter(
        user=request.user,
        return_date__isnull=True
    ).select_related('book')
    
    loan_history = BookLoan.objects.filter(
        user=request.user,
        return_date__isnull=False
    ).select_related('book').order_by('-return_date')[:5]
    
    # Get user's fine statistics
    outstanding_fines = Fine.objects.filter(
        user=request.user,
        payment_date__isnull=True
    ).select_related('loan', 'loan__book')
    
    paid_fines = Fine.objects.filter(
        user=request.user,
        payment_date__isnull=False
    ).select_related('loan', 'loan__book').order_by('-payment_date')[:5]
    
    context = {
        'form': form,
        'active_loans': active_loans,
        'loan_history': loan_history,
        'outstanding_fines': outstanding_fines,
        'paid_fines': paid_fines,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def password_change_view(request):
    if request.method == 'POST':
        # Handle password change logic here
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Your old password was entered incorrectly.')
            return redirect('accounts:password_change')
            
        if new_password1 != new_password2:
            messages.error(request, 'The two password fields did not match.')
            return redirect('accounts:password_change')
            
        request.user.set_password(new_password1)
        request.user.save()
        messages.success(request, 'Your password was successfully updated!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/password_change.html')

# API ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return self.serializer_class

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return User.objects.all()
        elif user.role == 'LIBRARIAN':
            return User.objects.filter(role='STUDENT')
        return User.objects.filter(id=user.id)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordChangeSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Wrong password"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"status": "password changed"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
