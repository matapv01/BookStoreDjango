# store/decorators.py

from functools import wraps
from django.http import JsonResponse
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

# Import model User tùy chỉnh của bạn
# Đảm bảo đường dẫn import này là chính xác dựa trên cấu trúc dự án của bạn
# Nếu User model nằm trong app 'store':
from .models import Users
# Nếu User model nằm trong app khác, ví dụ 'accounts':
# from accounts.models import Users
# Hoặc dùng cách của Django để lấy model động:
# from django.contrib.auth import get_user_model
# Users = get_user_model() # Cách này linh hoạt hơn nếu bạn thay đổi app chứa User model

def get_user_from_token(request):
    """
    Hàm trợ giúp để trích xuất và xác thực token từ header Authorization,
    sau đó lấy đối tượng User tương ứng.

    Args:
        request: Đối tượng HttpRequest.

    Returns:
        Tuple: (user, None) nếu thành công, (None, error_response) nếu thất bại.
               error_response là một đối tượng JsonResponse chứa lỗi.
    """
    # 1. Lấy header Authorization
    auth_header = request.headers.get('Authorization')

    # 2. Kiểm tra header có tồn tại và đúng định dạng 'Bearer <token>' không
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, JsonResponse(
            {'error': 'Authorization header missing or invalid format (Bearer required)'},
            status=401 # Unauthorized
        )

    # 3. Trích xuất chuỗi token
    try:
        token_string = auth_header.split(' ')[1]
    except IndexError:
        # Trường hợp header chỉ có 'Bearer ' mà không có token
        return None, JsonResponse({'error': 'Token missing in Authorization header'}, status=401)

    # 4. Xác thực token và lấy thông tin user
    try:
        # Tạo đối tượng AccessToken từ chuỗi token
        access_token = AccessToken(token_string)

        # Simple JWT tự động kiểm tra chữ ký và thời gian hết hạn khi bạn truy cập payload
        # Lấy user_id từ payload của token
        user_id = access_token[settings.SIMPLE_JWT['USER_ID_CLAIM']] # Sử dụng claim đã cấu hình trong settings

        # Lấy đối tượng User từ database dựa trên user_id
        # Dùng try-except để bắt lỗi nếu user không tồn tại
        try:
            user = Users.objects.get(id=user_id)
            # Kiểm tra xem tài khoản có active không
            if not user.is_active:
                return None, JsonResponse({'error': 'User account is disabled'}, status=403) # Forbidden
            # Trả về user nếu mọi thứ ổn
            return user, None
        except Users.DoesNotExist:
            return None, JsonResponse({'error': 'User associated with token not found'}, status=404) # Not Found

    # 5. Xử lý các lỗi liên quan đến token (không hợp lệ, hết hạn, lỗi định dạng)
    except (InvalidToken, TokenError) as e:
        # InvalidToken bao gồm cả lỗi hết hạn (TokenExpiredError)
        return None, JsonResponse({'error': 'Invalid or expired token', 'details': str(e)}, status=401)
    # 6. Bắt các lỗi không mong muốn khác
    except Exception as e:
        print(f"Unexpected Token Verification Error: {e}") # Ghi log lỗi ra console server
        import traceback
        traceback.print_exc() # In traceback đầy đủ
        return None, JsonResponse({'error': 'Could not process token due to server error'}, status=500)


def token_required(view_func):
    """
    Decorator để yêu cầu một Access Token hợp lệ trong header Authorization.
    Gắn đối tượng user đã xác thực vào request.user.
    """
    @wraps(view_func) # Giữ lại thông tin của view gốc (tên, docstring)
    def _wrapped_view(request, *args, **kwargs):
        # Gọi hàm trợ giúp để lấy user từ token
        user, error_response = get_user_from_token(request)

        # Nếu có lỗi (token không hợp lệ, user không tồn tại,...), trả về lỗi ngay lập tức
        if error_response:
            return error_response

        # Nếu thành công, gắn đối tượng user vào request để view có thể sử dụng
        request.user = user

        # Gọi hàm view gốc với request đã được bổ sung user
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def staff_token_required(view_func):
    """
    Decorator yêu cầu Access Token hợp lệ VÀ user phải là staff (is_staff=True).
    Gắn đối tượng user đã xác thực vào request.user.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Bước 1: Yêu cầu token hợp lệ và lấy user (giống như token_required)
        user, error_response = get_user_from_token(request)
        if error_response:
            return error_response

        # Bước 2: Kiểm tra thêm quyền staff của user
        if not user.is_staff:
            return JsonResponse(
                {'error': 'Staff permissions required to access this resource'},
                status=403 # Forbidden - Không có quyền
            )

        # Nếu user hợp lệ VÀ là staff, gắn user vào request
        request.user = user

        # Gọi hàm view gốc
        return view_func(request, *args, **kwargs)

    return _wrapped_view