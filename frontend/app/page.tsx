import Link from 'next/link';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Our Ecommerce Store
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Discover amazing products at great prices
        </p>
        <Link
          href="/products"
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Shop Now
        </Link>
      </div>

      <div className="grid md:grid-cols-3 gap-8 mt-12">
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Quality Products</h3>
          <p className="text-gray-600">We offer only the highest quality products from trusted brands.</p>
        </div>
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Fast Shipping</h3>
          <p className="text-gray-600">Quick and reliable shipping to get your orders to you fast.</p>
        </div>
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <h3 className="text-xl font-semibold mb-2">Secure Payments</h3>
          <p className="text-gray-600">Safe and secure payment processing for your peace of mind.</p>
        </div>
      </div>
    </div>
  );
}
