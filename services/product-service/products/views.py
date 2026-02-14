from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import subprocess
import os
from .models import Product
from .serializers import ProductSerializer

class ProductView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailView(APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def run_product_tests(request):
    """Run unit tests for the Product service"""
    try:
        # Run Django tests
        result = subprocess.run(
            ['python', 'manage.py', 'test', 'products.tests', '--verbosity=2'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            timeout=300
        )

        # Parse test output to extract statistics
        output = result.stdout + result.stderr
        lines = output.split('\n')

        total_tests = 0
        passed_tests = 0
        failed_tests = 0

        for line in lines:
            if line.startswith('Ran ') and ' tests' in line:
                # Extract "Ran X tests" information
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        total_tests = int(parts[1])
                    except ValueError:
                        pass
            elif line.strip() == 'OK':
                passed_tests = total_tests
                failed_tests = 0
            elif 'FAILURES' in line or 'ERRORS' in line:
                # Try to extract failure count
                failed_tests = total_tests - passed_tests if total_tests > 0 else 0

        return Response({
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'output': output,
            'success': result.returncode == 0
        })

    except subprocess.TimeoutExpired:
        return Response({
            'error': 'Test execution timed out',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'output': 'Test execution timed out after 5 minutes'
        }, status=408)

    except Exception as e:
        return Response({
            'error': str(e),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'output': f'Error running tests: {str(e)}'
        }, status=500)
