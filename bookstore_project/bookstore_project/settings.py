# bookstore_project/settings.py
from pathlib import Path
import os
from datetime import timedelta # <<< THÊM: Cần thiết cho SIMPLE_JWT lifetimes

from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = 'vi' # Ngôn ngữ mặc định là tiếng Việt

LANGUAGES = [
    ('en', _('English')),
    ('vi', _('Vietnamese')),
]

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Đường dẫn tới các file .po chứa bản dịch
LOCALE_PATHS = [
    BASE_DIR / 'locale', # Tạo thư mục 'locale' ở thư mục gốc dự án
]



# SECURITY WARNING: keep the secret key used in production secret!
# !!! Nhớ thay thế bằng secret key thực sự của bạn và giữ bí mật !!!
SECRET_KEY = 'si1d5z=1s^xy2gi)$tnvb*fg8be#(^l@$7ve6bteplzgepx+1)'

# SECURITY WARNING: don't run with debug turned on in production!
# !!! Đặt thành False khi triển khai lên môi trường production !!!
DEBUG = True

ALLOWED_HOSTS = [] # <<< THÊM: Cần cấu hình cho môi trường production (ví dụ: ['yourdomain.com', 'www.yourdomain.com'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage', # <<< THÊM CHO DJANGO-CLOUDINARY-STORAGE
    'cloudinary',
    'store',  # Ứng dụng của bạn
    'crispy_forms',
    # --- Thêm cho DRF và Simple JWT ---
    'rest_framework', # <<< ĐÃ CÓ (Tốt)
    'rest_framework_simplejwt', # <<< ĐÃ CÓ (Tốt)
    'rest_framework_simplejwt.token_blacklist', # <<< ĐÃ CÓ (Tùy chọn, dùng để thu hồi token)
    # ------------------------------------
]

# --- CLOUDINARY CONFIGURATION ---
# Thay thế bằng thông tin tài khoản Cloudinary của bạn
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dqvede4dm',        # <<< THAY BẰNG CLOUD NAME CỦA BẠN
    'API_KEY': '433246166292514',              # <<< THAY BẰNG API KEY CỦA BẠN
    'API_SECRET': 'H2zTUaWOAsRhg7CzVB4g0UtUUlk',        # <<< THAY BẰNG API SECRET CỦA BẠN
    'SECURE': True,                         # Sử dụng HTTPS cho URL hình ảnh
    'MEDIA_TAG': 'img',                     # Thẻ HTML mặc định khi render ảnh (tùy chọn)
}

# Cấu hình trực tiếp cho thư viện cloudinary
import cloudinary
cloudinary.config(
    cloud_name='dqvede4dm',
    api_key='433246166292514',
    api_secret='H2zTUaWOAsRhg7CzVB4g0UtUUlk',
    secure=True
)

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Giữ lại nếu dùng admin hoặc các phần khác của session
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # Giữ lại trừ khi bạn chắc chắn muốn tắt CSRF toàn cục
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Giữ lại cho admin và các hàm authenticate
    'django.contrib.messages.middleware.MessageMiddleware', # Giữ lại nếu dùng messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bookstore_project.urls'

# --- Thêm cấu hình Django REST Framework ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication', # <<< BẮT BUỘC: Xác thực bằng JWT
        'rest_framework.authentication.SessionAuthentication', # <<< THÊM (Khuyến nghị): Để dùng song song với admin/session nếu cần
    ),
    # Bạn có thể thêm các cài đặt DRF khác ở đây (ví dụ: permissions, pagination)
    # 'DEFAULT_PERMISSION_CLASSES': [
    #     'rest_framework.permissions.IsAuthenticatedOrReadOnly', # Ví dụ: Yêu cầu token cho các hành động ghi (POST, PUT, DELETE)
    # ]
}
# -----------------------------------------

# --- Thêm cấu hình Simple JWT ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # Thời gian sống của Access Token (ví dụ: 60 phút)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # Thời gian sống của Refresh Token (ví dụ: 1 ngày)
    'ROTATE_REFRESH_TOKENS': True, # <<< QUAN TRỌNG: Tạo refresh token mới khi dùng refresh token cũ
    'BLACKLIST_AFTER_ROTATION': True, # <<< QUAN TRỌNG: Thu hồi refresh token cũ sau khi rotation (cần blacklist app)
    'UPDATE_LAST_LOGIN': True,     # Cập nhật trường last_login của user khi refresh token

    'ALGORITHM': 'HS256',          # Thuật toán ký token
    'SIGNING_KEY': SECRET_KEY,     # Dùng SECRET_KEY của Django (mặc định)
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',), # Kiểu header xác thực mong đợi (ví dụ: "Authorization: Bearer <token>")
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION', # Tên header trong request.META
    'USER_ID_FIELD': 'id',         # Tên trường định danh user trong model
    'USER_ID_CLAIM': 'user_id',    # Tên claim chứa user ID trong payload token

    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    # Cấu hình cho Sliding Tokens (nếu bạn muốn dùng)
    # 'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    # 'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    # 'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
# --------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookstore_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

LANGUAGE_CODE = 'en-us' # <<< SỬA ĐỔI (Có thể đổi thành 'vi' nếu muốn giao diện admin tiếng Việt)
TIME_ZONE = 'Asia/Ho_Chi_Minh' # <<< ĐÃ CÓ (Tốt)
USE_I18N = True
USE_TZ = True # <<< QUAN TRỌNG: Nên giữ True khi dùng Timezone

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# STATIC_ROOT = BASE_DIR / 'staticfiles' # Bỏ comment dòng này khi chạy collectstatic cho production

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_TEMPLATE_PACK = 'bootstrap4' # <<< ĐÃ CÓ (Tốt)

# Custom User Model
AUTH_USER_MODEL = 'store.Users' # <<< ĐÃ CÓ (Rất quan trọng cho JWT)