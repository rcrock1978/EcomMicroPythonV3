'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import axios from 'axios';
import { useCartStore } from '../../../lib/cart-store';

interface Product {
  id: number;
  name: string;
  description: string;
  price: string;
}

const ProductDetailPage = () => {
  const params = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const addItem = useCartStore((state) => state.addItem);

  useEffect(() => {
    if (params.id) {
      axios.get(`http://localhost:8001/api/products/${params.id}/`).then(res => setProduct(res.data));
    }
  }, [params.id]);

  const handleAddToCart = () => {
    if (product) {
      addItem(product);
      alert('Added to cart!');
    }
  };

  if (!product) {
    return <div className="container mx-auto px-4 py-8">Loading...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-8">
        <h1 className="text-3xl font-bold mb-4">{product.name}</h1>
        <p className="text-gray-600 mb-6">{product.description}</p>
        <p className="text-4xl font-bold text-blue-600 mb-6">${product.price}</p>
        <button
          onClick={handleAddToCart}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors text-lg"
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
};

export default ProductDetailPage;