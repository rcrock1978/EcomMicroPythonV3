'use client';

import Link from 'next/link';
import { useCartStore } from '../lib/cart-store';

const Header = () => {
  const items = useCartStore((state) => state.items);
  const itemCount = items.reduce((total, item) => total + item.quantity, 0);

  return (
    <header className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold">
          Ecommerce Store
        </Link>
        <nav className="space-x-6 flex items-center">
          <Link href="/" className="hover:text-blue-200">
            Home
          </Link>
          <Link href="/products" className="hover:text-blue-200">
            Products
          </Link>
          <Link href="/cart" className="hover:text-blue-200 relative">
            Cart
            {itemCount > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                {itemCount}
              </span>
            )}
          </Link>
          <Link href="/profile" className="hover:text-blue-200">
            Profile
          </Link>
          <Link href="/admin" className="hover:text-blue-200">
            Admin
          </Link>
          <Link href="/login" className="hover:text-blue-200">
            Login
          </Link>
          <Link href="/register" className="hover:text-blue-200">
            Register
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;