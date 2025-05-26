from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import Category, Product, UserProfile
from admin_panel.models import SystemSettings
from decimal import Decimal
import cloudinary.uploader
import os

class Command(BaseCommand):
    help = 'Creates sample data for the bookstore'

    def handle(self, *args, **kwargs):
        # Create system settings
        settings = SystemSettings.objects.create(
            site_name='BookStore',
            site_description='Your Online Bookstore',
            contact_email='contact@bookstore.com',
            phone_number='0123456789',
            address='123 Book Street, Reading City',
            facebook_url='https://facebook.com/bookstore',
            twitter_url='https://twitter.com/bookstore',
            instagram_url='https://instagram.com/bookstore',
            maintenance_mode=False,
            is_active=True
        )

        # Create categories with sample images
        categories = {
            'Fiction': {
                'description': 'Fiction books including novels and short stories',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/fiction.jpg'
            },
            'Non-Fiction': {
                'description': 'Non-fiction books including biographies and educational books',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/non-fiction.jpg'
            },
            'Science': {
                'description': 'Science books covering various scientific topics',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/science.jpg'
            },
            'Technology': {
                'description': 'Technology books about programming and digital world',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/technology.jpg'
            }
        }

        created_categories = {}
        for name, data in categories.items():
            # Upload category image to Cloudinary
            try:
                result = cloudinary.uploader.upload(
                    data['image'],
                    folder="bookstore/categories",
                    public_id=name.lower().replace(' ', '_'),
                    resource_type="image"
                )
                image_url = result['secure_url']
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not upload image for {name}: {str(e)}'))
                # Use a default image if upload fails
                image_url = 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/default.jpg'
            
            category = Category.objects.create(
                name=name,
                description=data['description'],
                image=image_url,
                slug=name.lower().replace(' ', '-')
            )
            created_categories[name] = category

        # Create sample products
        products_data = [
            {
                'name': 'The Great Adventure',
                'description': 'An exciting adventure novel',
                'price': Decimal('19.99'),
                'stock': 50,
                'category': 'Fiction',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/adventure.jpg'
            },
            {
                'name': 'Python Programming',
                'description': 'Learn Python programming from scratch',
                'price': Decimal('29.99'),
                'stock': 30,
                'category': 'Technology',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/python.jpg'
            },
            {
                'name': 'Space Exploration',
                'description': 'Discover the mysteries of space',
                'price': Decimal('24.99'),
                'stock': 25,
                'category': 'Science',
                'image': 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/space.jpg'
            }
        ]

        for product_data in products_data:
            # Upload product image to Cloudinary
            try:
                result = cloudinary.uploader.upload(
                    product_data['image'],
                    folder="bookstore/products",
                    public_id=product_data['name'].lower().replace(' ', '_'),
                    resource_type="image"
                )
                image_url = result['secure_url']
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not upload image for {product_data["name"]}: {str(e)}'))
                # Use a default image if upload fails
                image_url = 'https://res.cloudinary.com/dqvede4dm/image/upload/v1/sample/book-covers/default.jpg'
            
            Product.objects.create(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock'],
                category=created_categories[product_data['category']],
                image=image_url,
                slug=product_data['name'].lower().replace(' ', '-')
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample data')) 