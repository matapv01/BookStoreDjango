# store/management/commands/create_sample_data.py

import random
import uuid
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
from django.utils import timezone # Import timezone

# Import các model từ app 'store'
# Đảm bảo đường dẫn import đúng nếu cấu trúc thư mục khác
from store.models import Users, Category, Books, Order, OrderItem, Cart, CartBooks

# Danh sách mô tả sách mẫu
BOOK_DESCRIPTIONS = [
    "Một khám phá hấp dẫn về {topic} sẽ khiến bạn bị cuốn hút từ đầu đến cuối.",
    "Khám phá những bí ẩn của {topic} trong cuốn cẩm nang toàn diện này.",
    "Phân tích chuyên sâu về {topic} với các ví dụ thực tế.",
    "Hướng dẫn cơ bản để hiểu {topic} trong bối cảnh hiện đại.",
    "Giới thiệu thân thiện cho người mới bắt đầu về {topic} với lời giải thích rõ ràng.",
    "Các khái niệm nâng cao về {topic} được giải thích một cách đơn giản.",
    "Mọi thứ bạn cần biết về {topic} trong một cuốn sách.",
    "Cách tiếp cận thực tế để làm chủ {topic} với các bài tập thực hành.",
    "Những phát triển mới nhất trong lĩnh vực {topic} được trình bày bởi các chuyên gia.",
    "Một góc nhìn mang tính cách mạng về {topic} làm thay đổi mọi thứ."
]

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu để kiểm thử ứng dụng cửa hàng sách'

    # --- Các hàm helper ---
    def generate_address(self):
        streets = ['Nguyễn Huệ', 'Lê Lợi', 'Đồng Khởi', 'Lý Tự Trọng', 'Lê Duẩn', 'Pasteur', 'Nam Kỳ Khởi Nghĩa', 'Hai Bà Trưng', 'Lê Thánh Tôn', 'Nguyễn Du']
        districts = ['Quận 1', 'Quận 2', 'Quận 3', 'Quận 4', 'Quận 5', 'Bình Thạnh', 'Thủ Đức', 'Phú Nhuận', 'Tân Bình', 'Gò Vấp']
        return f'{random.randint(1,200)} Đường {random.choice(streets)}, {random.choice(districts)}, TP.HCM'

    def generate_book_title(self, category_name, index):
        topics = {
            'Fiction': ['Bí ẩn', 'Lãng mạn', 'Phiêu lưu', 'Kỳ ảo', 'Giật gân', 'Lịch sử', 'Đương đại', 'Văn học', 'Kinh dị', 'Kịch'],
            'Science Fiction': ['Du hành không gian', 'Cyberpunk', 'Du hành thời gian', 'Phản địa đàng', 'Trí tuệ nhân tạo', 'Người ngoài hành tinh', 'Robot', 'Thực tế ảo', 'Hậu tận thế', 'Sao Hỏa'],
            'Technology': ['Lập trình', 'Phát triển Web', 'Khoa học dữ liệu', 'AI', 'Điện toán đám mây', 'Bảo mật', 'Ứng dụng di động', 'DevOps', 'Blockchain', 'IoT'],
            'Business': ['Lãnh đạo', 'Marketing', 'Tài chính', 'Chiến lược', 'Quản lý', 'Khởi nghiệp', 'Đổi mới', 'Kinh tế học', 'Startup', 'Bán hàng'],
            'Self Help': ['Năng suất', 'Chánh niệm', 'Thành công', 'Hạnh phúc', 'Sức khỏe', 'Mối quan hệ', 'Sự nghiệp', 'Phát triển cá nhân', 'Động lực', 'Thói quen']
        }
        topic_list = topics.get(category_name, ['Chủ đề chung'])
        topic = random.choice(topic_list)
        adjectives = ['Thiết yếu', 'Toàn tập', 'Tuyệt đỉnh', 'Thực tế', 'Hiện đại', 'Nâng cao', 'Cơ bản', 'Chuyên nghiệp', 'Toàn diện', 'Nhanh chóng']
        patterns = [
            "Cẩm nang {adj} về {topic}",
            "Làm chủ {topic}",
            "Tìm hiểu về {topic}",
            "{topic}: Tiếp cận {adj}",
            "{adj} {topic}",
            "Nghệ thuật của {topic}",
            "Nguyên tắc cơ bản của {topic}",
            "Khám phá {topic}",
            "{topic} trong thực tế",
            "Sổ tay {topic}"
        ]
        pattern = random.choice(patterns)
        try:
            # Đảm bảo pattern là chuỗi trước khi format
            if isinstance(pattern, str):
                return pattern.format(adj=random.choice(adjectives), topic=topic)
            else:
                # Xử lý trường hợp pattern không phải chuỗi (dự phòng)
                print(f"Warning: Invalid pattern chosen: {pattern}. Using default title.")
                return f"Sách về {topic} #{index+1}"
        except KeyError as e:
            # Xử lý lỗi nếu placeholder trong pattern không khớp (ví dụ: {ad} thay vì {adj})
             print(f"Warning: Formatting error for pattern '{pattern}' with topic '{topic}': {e}. Using default title.")
             return f"Sách về {topic} #{index+1}"

    # ------------------------------------------------------

    @transaction.atomic # Đảm bảo tất cả các thao tác là một transaction
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('--- Bắt đầu tạo dữ liệu mẫu ---'))

        # Cleanup old data
        self.stdout.write('Đang xóa dữ liệu cũ...')
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        CartBooks.objects.all().delete()
        Cart.objects.all().delete()
        Books.objects.all().delete()
        Category.objects.all().delete()
        Users.objects.filter(is_superuser=False).delete()
        self.stdout.write('Xóa dữ liệu cũ thành công.')

        # 1. Create/Get Users
        self.stdout.write('Đang tạo người dùng...')
        try:
            superuser, created = Users.objects.get_or_create(
                email='admin@example.com',
                defaults={'name': 'Quản trị viên hệ thống', 'is_staff': True, 'is_superuser': True}
            )
            if created:
                superuser.set_password('admin123')
                superuser.save()
                self.stdout.write(self.style.SUCCESS('Đã tạo superuser admin@example.com'))
            else:
                self.stdout.write('Superuser admin@example.com đã tồn tại.')

            staff_users = []
            staff_roles = ['Quản lý nội dung', 'Quản lý bán hàng', 'Quản lý kho', 'Chăm sóc khách hàng']
            for i, role in enumerate(staff_roles):
                staff_email = f'staff{i+1}@example.com'
                staff, created = Users.objects.get_or_create(
                    email=staff_email,
                    defaults={'name': role, 'is_staff': True, 'type': 'admin'}
                )
                if created:
                    staff.set_password('staff123')
                    staff.save()
                staff_users.append(staff)
            self.stdout.write(f'Đảm bảo {len(staff_users)} người dùng staff tồn tại.')

            regular_users = []
            for i in range(15):
                user_email = f'user{i+1}@example.com'
                user, created = Users.objects.get_or_create(
                    email=user_email, defaults={'name': f'Người dùng {i+1}'}
                )
                if created:
                    user.set_password('user123')
                    user.save()
                regular_users.append(user)
            self.stdout.write(f'Đảm bảo {len(regular_users)} người dùng thường tồn tại.')
        except Exception as e:
            raise CommandError(f"Lỗi khi tạo người dùng: {e}")

        # 2. Create Categories
        self.stdout.write('Đang tạo danh mục...')
        try:
            category_data = [
                ('Fiction', 'Sách hư cấu cổ điển và đương đại'), ('Science Fiction', 'Tiểu thuyết tương lai và khoa học viễn tưởng'),
                ('Mystery', 'Truyện trinh thám và bí ẩn'), ('Romance', 'Truyện tình yêu và các mối quan hệ'),
                ('Technology', 'Sách về máy tính và công nghệ'), ('Science', 'Chủ đề khoa học và nghiên cứu'),
                ('Business', 'Sách kinh doanh và kinh tế'), ('Self Help', 'Hướng dẫn phát triển cá nhân'),
                ('Biography', 'Câu chuyện cuộc đời và hồi ký'), ('History', 'Sự kiện và phân tích lịch sử'),
                ('Art', 'Lịch sử và kỹ thuật nghệ thuật'), ('Design', 'Thiết kế đồ họa và nội thất'),
                ('Cooking', 'Sách dạy nấu ăn và nghệ thuật ẩm thực'), ('Travel', 'Hướng dẫn và trải nghiệm du lịch'),
                ('Children', 'Sách cho độc giả nhỏ tuổi')
            ]
            categories = []
            category_map = {}
            for name, desc in category_data:
                category, created = Category.objects.get_or_create(
                    name=name, defaults={'description': desc} # Giả sử có description
                )
                categories.append(category)
                category_map[name] = category
            self.stdout.write(f'Đảm bảo {len(categories)} danh mục tồn tại.')
        except Exception as e:
             raise CommandError(f"Lỗi khi tạo danh mục: {e}")

        # 3. Create Books
        self.stdout.write('Đang tạo sách...')
        books = []
        BOOKS_PER_CATEGORY = 20
        try:
            for category in categories:
                created_count_for_cat = 0
                for i in range(BOOKS_PER_CATEGORY):
                    price = Decimal(random.uniform(9.99, 59.99)).quantize(Decimal('0.01'))
                    stock = random.randint(5, 150)
                    sold = random.randint(0, stock // 3) # Bán ít hơn

                    title = self.generate_book_title(category.name, i)
                    if not title: continue # Bỏ qua nếu không tạo được title

                    if Books.objects.filter(category=category, title=title).exists():
                        continue

                    description_topic = category_map.get(category.name, Category(name='chung')).name.lower() # Lấy tên gốc hoặc mặc định
                    description = random.choice(BOOK_DESCRIPTIONS)
                    if isinstance(description, str): # Đảm bảo description là chuỗi
                         description = description.format(topic=description_topic)
                    else:
                         description = f"Mô tả sách về {description_topic}"


                    book = Books.objects.create(
                        title=title, description=description, price=price,
                        stock=stock, sold=sold, category=category
                    )
                    books.append(book)
                    created_count_for_cat += 1

                if hasattr(category, 'total_books'):
                    category.total_books = Books.objects.filter(category=category).count()
                    category.save(update_fields=['total_books'])

            self.stdout.write(f'Đã tạo {len(books)} cuốn sách mới.')
        except Exception as e:
             raise CommandError(f"Lỗi khi tạo sách: {e}")


        # 4. Create Orders
        self.stdout.write('Đang tạo đơn hàng...')
        NUM_ORDERS = 30
        created_orders = []
        if not books:
             self.stdout.write(self.style.WARNING('Không có sách để tạo đơn hàng.'))
        else:
            try:
                for i in range(NUM_ORDERS):
                    user = random.choice(regular_users + staff_users)
                    status = random.choice([Order.PROCESSING, Order.COMPLETED, Order.CANCELLED])
                    payment = random.choice([Order.UNPAID, Order.PAID, Order.REFUNDED])
                    if status == Order.COMPLETED: payment = Order.PAID
                    if status == Order.CANCELLED and payment == Order.PAID: payment = Order.REFUNDED
                    if status != Order.COMPLETED and payment == Order.REFUNDED: payment = Order.UNPAID

                    order = Order(
                        user=user, status=status, payment_status=payment,
                        shipping_address=self.generate_address(),
                    )
                    order.save() # Lưu để có ID và number

                    order_total = Decimal('0.00')
                    num_book_types = random.randint(2, min(5, len(books)))
                    order_books_sample = random.sample(books, num_book_types)

                    for book in order_books_sample:
                        quantity = random.randint(1, 3)
                        # Chỉ tạo item nếu sách còn hàng HOẶC đơn hàng chưa hoàn thành
                        # (logic này cho phép đặt hàng chờ nếu muốn)
                        if book.stock >= quantity or status != Order.COMPLETED:
                             try:
                                # Tạo OrderItem, price_at_purchase sẽ tự lấy
                                order_item = OrderItem.objects.create(order=order, book=book, quantity=quantity)
                                order_total += order_item.price_at_purchase * quantity

                                # Chỉ cập nhật stock/sold nếu đơn hoàn thành và item được tạo thành công
                                if status == Order.COMPLETED:
                                    # Cập nhật trực tiếp để tránh race condition
                                    updated_count = Books.objects.filter(pk=book.pk, stock__gte=quantity).update(
                                        stock=models.F('stock') - quantity,
                                        sold=models.F('sold') + quantity
                                    )
                                    # Nếu không update được (do stock thay đổi), cần xử lý (ví dụ: rollback, báo lỗi)
                                    # Ở đây tạm bỏ qua xử lý race condition phức tạp trong script tạo data
                                    # if updated_count == 0:
                                    #     print(f"Warning: Could not update stock for book {book.id} in order {order.id}")
                             except IntegrityError as ie:
                                 print(f"Warning: Could not create OrderItem for book {book.id} in order {order.id}. Error: {ie}")


                    # Cập nhật tổng tiền cuối cùng
                    order.total_amount = order_total
                    order.save(update_fields=['total_amount'])
                    created_orders.append(order)

                self.stdout.write(f'Đã tạo {len(created_orders)} đơn hàng.')
            except Exception as e:
                raise CommandError(f"Lỗi khi tạo đơn hàng: {e}")


        # 5. Create Carts
        self.stdout.write('Đang tạo giỏ hàng...')
        created_carts = 0
        if not books:
             self.stdout.write(self.style.WARNING('Không có sách để tạo giỏ hàng.'))
        else:
            try:
                for user in regular_users:
                    if random.random() < 0.7:
                        cart, cart_created = Cart.objects.get_or_create(user=user)
                        if cart_created: created_carts += 1

                        num_books_in_cart = random.randint(1, min(4, len(books)))
                        existing_book_ids_in_cart = set(CartBooks.objects.filter(cart=cart).values_list('book_id', flat=True))
                        available_books_for_cart = [b for b in books if b.id not in existing_book_ids_in_cart]
                        num_to_sample_cart = min(num_books_in_cart, len(available_books_for_cart))

                        if num_to_sample_cart > 0:
                            cart_books_to_add_sample = random.sample(available_books_for_cart, num_to_sample_cart)
                            for book in cart_books_to_add_sample:
                                quantity = random.randint(1, 3)
                                if quantity <= book.stock:
                                    CartBooks.objects.get_or_create(
                                        cart=cart, book=book, defaults={'quantity': quantity}
                                    )

                self.stdout.write(f'Đảm bảo giỏ hàng tồn tại cho khoảng {created_carts} người dùng thường.')
            except Exception as e:
                 raise CommandError(f"Lỗi khi tạo giỏ hàng: {e}")


        # Print final summary
        self.stdout.write(self.style.SUCCESS(
            f'\n--- Tạo dữ liệu mẫu hoàn thành ---'
            f'\n- Users: {Users.objects.count()}'
            f'\n- Categories: {Category.objects.count()}'
            f'\n- Books: {Books.objects.count()}'
            f'\n- Orders: {Order.objects.count()}'
            f'\n- Carts: {Cart.objects.count()}'
            f'\n- Cart Items: {CartBooks.objects.count()}'
            f'\n- Order Items: {OrderItem.objects.count()}'
        ))