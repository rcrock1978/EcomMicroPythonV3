from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_active', 'date_joined']

    def validate(self, data):
        # Password is required for creation, optional for updates
        if not self.instance and not data.get('password'):
            raise serializers.ValidationError({'password': 'This field is required.'})
        return data