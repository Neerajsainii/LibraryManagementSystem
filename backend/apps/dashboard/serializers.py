from rest_framework import serializers
from .models import DailyStats, BookActivity

class DailyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStats
        fields = '__all__'
        read_only_fields = ('created_at',)

class BookActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookActivity
        fields = '__all__'
        read_only_fields = ('created_at',)