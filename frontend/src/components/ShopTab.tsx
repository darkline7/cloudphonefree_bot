import React, { useState } from 'react';
import type { ProductItem, OrderItem } from '../types';
import { ShoppingBag, Plus, Trash2, Edit, Package } from 'lucide-react';

interface Props {
  products: ProductItem[];
  orders: OrderItem[];
  onCreateProduct: (name: string, price: number, description?: string) => Promise<void>;
  onUpdateProduct: (id: number, name: string, price: number, description: string | null, isActive: boolean) => Promise<void>;
  onDeleteProduct: (id: number) => Promise<void>;
  onAddStock: (productId: number, items: string[]) => Promise<void>;
}

export const ShopTab: React.FC<Props> = ({
  products,
  orders,
  onCreateProduct,
  onUpdateProduct,
  onDeleteProduct,
  onAddStock,
}) => {
  const [subTab, setSubTab] = useState<'products' | 'orders'>('products');
  const [showProductModal, setShowProductModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<ProductItem | null>(null);
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');
  const [isActive, setIsActive] = useState(true);

  const [stockModal, setStockModal] = useState<{ isOpen: boolean; product: ProductItem | null }>({
    isOpen: false,
    product: null,
  });
  const [stockInput, setStockInput] = useState('');
  const [stockList, setStockList] = useState<{ id: number; data: string; is_sold: boolean; order_id: number | null }[]>([]);
  const [loadingStock, setLoadingStock] = useState(false);

  const openCreateModal = () => {
    setEditingProduct(null);
    setName('');
    setPrice('');
    setDescription('');
    setIsActive(true);
    setShowProductModal(true);
  };

  const openEditModal = (p: ProductItem) => {
    setEditingProduct(p);
    setName(p.name);
    setPrice(p.price.toString());
    setDescription(p.description || '');
    setIsActive(p.is_active);
    setShowProductModal(true);
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    const numPrice = parseInt(price);
    if (!name || isNaN(numPrice)) return;
    if (editingProduct) {
      await onUpdateProduct(editingProduct.id, name, numPrice, description || null, isActive);
    } else {
      await onCreateProduct(name, numPrice, description || undefined);
    }
    setShowProductModal(false);
  };

  const openStockModal = async (p: ProductItem) => {
    setStockModal({ isOpen: true, product: p });
    setStockInput('');
    setLoadingStock(true);
    try {
      const res = await fetch(`/api/products/${p.id}/stock`);
      if (res.ok) setStockList(await res.json());
    } finally {
      setLoadingStock(false);
    }
  };

  const handleAddStockSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stockModal.product || !stockInput.trim()) return;
    const lines = stockInput.split('\n').map((l) => l.trim()).filter(Boolean);
    await onAddStock(stockModal.product.id, lines);
    setStockInput('');
    const res = await fetch(`/api/products/${stockModal.product.id}/stock`);
    if (res.ok) setStockList(await res.json());
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSubTab('products')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
              subTab === 'products'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            Quản Lý Sản Phẩm & Kho ({products.length})
          </button>
          <button
            onClick={() => setSubTab('orders')}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
              subTab === 'orders'
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            Đơn Hàng Đã Bán ({orders.length})
          </button>
        </div>

        {subTab === 'products' && (
          <button
            onClick={openCreateModal}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-bold flex items-center gap-2 shadow-lg shadow-emerald-500/25 hover:from-emerald-600 hover:to-teal-700 transition cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Thêm Sản Phẩm Mới
          </button>
        )}
      </div>

      {subTab === 'products' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((p) => (
            <div
              key={p.id}
              className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between backdrop-blur-xl relative group hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-lg text-slate-100">{p.name}</h3>
                  <span
                    className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                      p.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    }`}
                  >
                    {p.is_active ? 'Đang bán' : 'Tạm ẩn'}
                  </span>
                </div>

                <p className="text-2xl font-black text-emerald-400 mt-2">
                  {p.price.toLocaleString()}đ
                </p>

                <p className="text-sm text-slate-400 mt-2 line-clamp-2">
                  {p.description || 'Chưa có mô tả'}
                </p>

                <div className="mt-4 flex items-center gap-2 text-sm">
                  <span className="text-slate-400">Tồn kho:</span>
                  <span className={`font-bold px-2 py-0.5 rounded-lg text-xs ${p.stock_count > 0 ? 'bg-indigo-500/20 text-indigo-300' : 'bg-rose-500/20 text-rose-300'}`}>
                    {p.stock_count} tài khoản
                  </span>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between gap-2">
                <button
                  onClick={() => openStockModal(p)}
                  className="px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500/20 text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
                >
                  <Package className="w-3.5 h-3.5" />
                  Kho Hàng ({p.stock_count})
                </button>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => openEditModal(p)}
                    className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 transition cursor-pointer"
                    title="Chỉnh sửa"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onDeleteProduct(p.id)}
                    className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition cursor-pointer"
                    title="Xóa sản phẩm"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {products.length === 0 && (
            <div className="col-span-full py-12 text-center text-slate-500 bg-slate-900/30 rounded-2xl border border-slate-800/50">
              <ShoppingBag className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Chưa có sản phẩm nào trong shop. Bấm "Thêm Sản Phẩm Mới" để bắt đầu.</p>
            </div>
          )}
        </div>
      )}
      {subTab === 'orders' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4">Mã Đơn</th>
                  <th className="px-6 py-4">Khách Hàng</th>
                  <th className="px-6 py-4">Sản Phẩm</th>
                  <th className="px-6 py-4">Giá Tiền</th>
                  <th className="px-6 py-4">Tài Khoản Đã Cấp</th>
                  <th className="px-6 py-4">Thời Gian</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {orders.map((o) => (
                  <tr key={o.id} className="hover:bg-slate-800/30 transition">
                    <td className="px-6 py-4 font-mono font-bold text-indigo-400">#{o.id}</td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-semibold text-slate-200">
                          {o.username ? `@${o.username}` : `User ${o.user_id}`}
                        </div>
                        <div className="text-xs text-slate-500 font-mono">ID: {o.user_id}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-200">{o.product_name}</td>
                    <td className="px-6 py-4 font-mono font-bold text-emerald-400">{o.price.toLocaleString()}đ</td>
                    <td className="px-6 py-4">
                      <code className="bg-slate-950 px-2.5 py-1 rounded-md text-xs font-mono text-amber-300 select-all border border-slate-800">
                        {o.account_data}
                      </code>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">{o.created_at || 'Vừa xong'}</td>
                  </tr>
                ))}
                {orders.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                      Chưa có giao dịch mua hàng nào.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {showProductModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-100 mb-4">
              {editingProduct ? 'Chỉnh Sửa Sản Phẩm' : 'Thêm Sản Phẩm Mới'}
            </h3>
            <form onSubmit={handleSaveProduct} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Tên Sản Phẩm</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ví dụ: UmoCloud 6H Full VIP"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Giá Bán (VNĐ)</label>
                <input
                  type="number"
                  required
                  min="0"
                  step="1000"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="Ví dụ: 5000"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Mô Tả Sản Phẩm</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Mô tả chi tiết..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              {editingProduct && (
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="isActive"
                    checked={isActive}
                    onChange={(e) => setIsActive(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-600 bg-slate-950 border-slate-800"
                  />
                  <label htmlFor="isActive" className="text-sm text-slate-300">
                    Bật bán sản phẩm này
                  </label>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowProductModal(false)}
                  className="px-4 py-2 rounded-xl text-sm text-slate-400 hover:bg-slate-800 transition cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
                >
                  Lưu Sản Phẩm
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {stockModal.isOpen && stockModal.product && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl p-6 shadow-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h3 className="text-lg font-bold text-slate-100">
                  Quản Lý Kho: {stockModal.product.name}
                </h3>
                <p className="text-xs text-slate-400">
                  Thêm tài khoản (mỗi dòng 1 tài khoản, VD: email|pass)
                </p>
              </div>
              <button
                onClick={() => setStockModal({ isOpen: false, product: null })}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <div className="py-4 space-y-4 overflow-y-auto flex-1">
              <form onSubmit={handleAddStockSubmit} className="space-y-2">
                <label className="block text-xs font-semibold text-slate-300">
                  Nhập thêm tài khoản vào kho:
                </label>
                <textarea
                  rows={4}
                  value={stockInput}
                  onChange={(e) => setStockInput(e.target.value)}
                  placeholder={`user1@mail.com|pass123\nuser2@mail.com|pass456`}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-emerald-300 focus:outline-none focus:border-indigo-500"
                />
                <div className="flex justify-end">
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/30 transition cursor-pointer"
                  >
                    + Nạp Thêm Vào Kho
                  </button>
                </div>
              </form>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Danh sách tài khoản ({stockList.length})
                </h4>
                <div className="max-h-60 overflow-y-auto border border-slate-800 rounded-xl divide-y divide-slate-800/60 bg-slate-950/60">
                  {stockList.map((item) => (
                    <div key={item.id} className="p-2.5 flex items-center justify-between text-xs font-mono">
                      <span className="text-slate-300 truncate max-w-md">{item.data}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.is_sold
                            ? 'bg-rose-500/20 text-rose-400'
                            : 'bg-emerald-500/20 text-emerald-400'
                        }`}
                      >
                        {item.is_sold ? `Đã bán (Đơn #${item.order_id})` : 'Sẵn sàng'}
                      </span>
                    </div>
                  ))}
                  {stockList.length === 0 && (
                    <div className="p-6 text-center text-slate-500 text-xs">
                      {loadingStock ? 'Đang tải...' : 'Kho trống'}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setStockModal({ isOpen: false, product: null })}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}


    </div>
  );
};
