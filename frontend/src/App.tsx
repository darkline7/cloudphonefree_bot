import { useState, useEffect, useCallback } from 'react';

import type { DashboardStats, UserItem, AccountItem, ProductItem, OrderItem, BankTransactionItem, AuthState } from './types';
import { StatCard } from './components/StatCard';
import { UsersTab } from './components/UsersTab';
import { AccountsTab } from './components/AccountsTab';
import { BroadcastTab } from './components/BroadcastTab';
import { ShopTab } from './components/ShopTab';
import { BankTab } from './components/BankTab';
import { Modals } from './components/Modals';
import { LoginPage } from './components/LoginPage';
import {
  Users,
  Zap,
  Key,
  LogOut,
  RefreshCw,
  Gift,
  Activity,
  Megaphone,
  ShoppingBag,
  Landmark,
} from 'lucide-react';

export function App() {
  const [auth, setAuth] = useState<AuthState>({ authenticated: false, username: null });
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [activeTab, setActiveTab] = useState<'users' | 'accounts' | 'shop' | 'bank' | 'broadcast'>('users');

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [accounts, setAccounts] = useState<AccountItem[]>([]);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [transactions, setTransactions] = useState<BankTransactionItem[]>([]);

  const [loading, setLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSyncingBank, setIsSyncingBank] = useState(false);

  // Modals state
  const [bonusModal, setBonusModal] = useState({ isOpen: false, userId: 0, currentBonus: 0 });
  const [balanceModal, setBalanceModal] = useState({ isOpen: false, userId: 0, currentBalance: 0 });
  const [messageModal, setMessageModal] = useState<{ isOpen: boolean; userId: number; username: string | null }>({
    isOpen: false,
    userId: 0,
    username: null,
  });

  const checkAuth = async () => {
    try {
      const res = await fetch('/api/auth/me');
      const data = await res.json();
      setAuth(data);
    } catch {
      setAuth({ authenticated: false, username: null });
    } finally {
      setIsCheckingAuth(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const loadData = useCallback(async () => {
    if (!auth.authenticated) return;
    setLoading(true);
    try {
      const [statsRes, usersRes, accountsRes, productsRes, ordersRes, bankRes] = await Promise.all([
        fetch('/api/dashboard/stats'),
        fetch('/api/users'),
        fetch('/api/accounts'),
        fetch('/api/products'),
        fetch('/api/orders'),
        fetch('/api/bank/transactions'),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (usersRes.ok) setUsers(await usersRes.json());
      if (accountsRes.ok) setAccounts(await accountsRes.json());
      if (productsRes.ok) setProducts(await productsRes.json());
      if (ordersRes.ok) setOrders(await ordersRes.json());
      if (bankRes.ok) setTransactions(await bankRes.json());
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [auth.authenticated]);

  useEffect(() => {
    if (auth.authenticated) {
      loadData();
    }
  }, [auth.authenticated, loadData]);


  const handleLogin = async (u: string, p: string): Promise<string | null> => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: u, password: p }),
      });
      const data = await res.json();
      if (res.ok) {
        setAuth({ authenticated: true, username: u });
        return null;
      }
      return data.detail || 'Đăng nhập thất bại';
    } catch {
      return 'Lỗi kết nối máy chủ';
    }
  };

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setAuth({ authenticated: false, username: null });
  };

  const handleUpdateBonus = async (userId: number, bonusTurns: number) => {
    try {
      const res = await fetch(`/api/users/${userId}/bonus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bonus_turns: bonusTurns }),
      });
      if (res.ok) {
        setUsers((prev) =>
          prev.map((u) => (u.user_id === userId ? { ...u, bonus_turns: bonusTurns } : u))
        );
        setBonusModal({ isOpen: false, userId: 0, currentBonus: 0 });
      }
    } catch (err) {
      console.error('Failed to update bonus:', err);
    }
  };

  const handleUpdateBalance = async (userId: number, balance: number) => {
    try {
      const res = await fetch(`/api/users/${userId}/balance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ balance }),
      });
      if (res.ok) {
        setUsers((prev) =>
          prev.map((u) => (u.user_id === userId ? { ...u, balance } : u))
        );
        setBalanceModal({ isOpen: false, userId: 0, currentBalance: 0 });
      }
    } catch (err) {
      console.error('Failed to update balance:', err);
    }
  };

  const handleSendMessage = async (userId: number, content: string): Promise<boolean> => {
    try {
      const res = await fetch(`/api/users/${userId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      return res.ok;
    } catch {
      return false;
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm(`Bạn có chắc chắn muốn xoá người dùng ${userId} và tất cả dữ liệu liên quan?`)) return;
    try {
      const res = await fetch(`/api/users/${userId}`, { method: 'DELETE' });
      if (res.ok) {
        setUsers((prev) => prev.filter((u) => u.user_id !== userId));
      }
    } catch (err) {
      console.error('Failed to delete user:', err);
    }
  };

  const handleGenerateAccount = async () => {
    setIsGenerating(true);
    try {
      const res = await fetch('/api/accounts/generate', { method: 'POST' });
      if (res.ok) {
        await loadData();
      }
    } catch (err) {
      console.error('Failed to generate account:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteAccount = async (accountId: number) => {
    if (!confirm(`Xoá tài khoản ID ${accountId}?`)) return;
    try {
      const res = await fetch(`/api/accounts/${accountId}`, { method: 'DELETE' });
      if (res.ok) {
        setAccounts((prev) => prev.filter((a) => a.id !== accountId));
      }
    } catch (err) {
      console.error('Failed to delete account:', err);
    }
  };

  const handleSendBroadcast = async (content: string, targetUserId?: number): Promise<boolean> => {
    try {
      const res = await fetch('/api/broadcast', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, target_user_id: targetUserId }),
      });
      return res.ok;
    } catch {
      return false;
    }
  };


  // Shop actions
  const handleCreateProduct = async (name: string, price: number, description?: string) => {
    try {
      const res = await fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, price, description }),
      });
      if (res.ok) {
        const prodRes = await fetch('/api/products');
        if (prodRes.ok) setProducts(await prodRes.json());
      }
    } catch (err) {
      console.error('Failed to create product:', err);
    }
  };

  const handleUpdateProduct = async (
    id: number,
    name: string,
    price: number,
    description: string | null,
    isActive: boolean
  ) => {
    try {
      const res = await fetch(`/api/products/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, price, description, is_active: isActive }),
      });
      if (res.ok) {
        const prodRes = await fetch('/api/products');
        if (prodRes.ok) setProducts(await prodRes.json());
      }
    } catch (err) {
      console.error('Failed to update product:', err);
    }
  };

  const handleDeleteProduct = async (id: number) => {
    if (!confirm('Xác nhận xóa sản phẩm này cùng toàn bộ tồn kho chưa bán?')) return;
    try {
      const res = await fetch(`/api/products/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setProducts((prev) => prev.filter((p) => p.id !== id));
      }
    } catch (err) {
      console.error('Failed to delete product:', err);
    }
  };

  const handleAddStock = async (productId: number, items: string[]) => {
    try {
      const res = await fetch(`/api/products/${productId}/stock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });
      if (res.ok) {
        const prodRes = await fetch('/api/products');
        if (prodRes.ok) setProducts(await prodRes.json());
      }
    } catch (err) {
      console.error('Failed to add stock:', err);
    }
  };

  const handleSyncBank = async () => {
    setIsSyncingBank(true);
    try {
      await fetch('/api/bank/sync', { method: 'POST' });
      await loadData();
    } catch (err) {
      console.error('Failed to sync bank:', err);
    } finally {
      setIsSyncingBank(false);
    }
  };
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Activity className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (!auth.authenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }


  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-black text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                UmoCloud Admin Panel
              </h1>
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Auto ACB QR & Cloud System
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              disabled={loading}
              className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-all cursor-pointer"
              title="Làm mới dữ liệu"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            </button>

            <div className="h-6 w-px bg-slate-800" />

            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-slate-200">{auth.username}</div>
              <div className="text-[10px] text-emerald-400">Quản trị viên</div>
            </div>

            <button
              onClick={handleLogout}
              className="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition-all cursor-pointer"
              title="Đăng xuất"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <StatCard
            title="Tổng Người Dùng"
            value={stats?.total_users ?? 0}
            icon={Users}
            color="blue"
            subtitle="Đã đăng ký bot Telegram"
          />
          <StatCard
            title="Tài Khoản Đã Tạo"
            value={stats?.total_accounts ?? 0}
            icon={Key}
            color="green"
            subtitle="Cấp tự động qua WillClouds"
          />

          <StatCard
            title="Lượt Thưởng Tích Lũy"
            value={`+${stats?.total_bonus_awarded ?? 0}`}
            icon={Gift}
            color="amber"
            subtitle="Chính sách +5 lượt/ref"
          />
        </div>
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4 overflow-x-auto">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'users'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Users className="w-4 h-4" />
            Người Dùng ({users.length})
          </button>

          <button
            onClick={() => setActiveTab('shop')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'shop'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <ShoppingBag className="w-4 h-4" />
            Cửa Hàng ({products.length})
          </button>

          <button
            onClick={() => setActiveTab('bank')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'bank'
                ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Landmark className="w-4 h-4" />
            Lịch Sử Auto ACB ({transactions.length})
          </button>

          <button
            onClick={() => setActiveTab('accounts')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'accounts'
                ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/25'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Key className="w-4 h-4" />
            Lịch Sử Tạo Miễn Phí ({accounts.length})
          </button>

          <button
            onClick={() => setActiveTab('broadcast')}
            className={`px-5 py-2.5 rounded-xl text-sm font-bold flex items-center gap-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'broadcast'
                ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/25'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            <Megaphone className="w-4 h-4" />
            Phát Sóng Thông Báo
          </button>
        </div>

        {activeTab === 'users' && (
          <UsersTab
            users={users}
            onUpdateBonus={(uid, cur) => setBonusModal({ isOpen: true, userId: uid, currentBonus: cur })}
            onUpdateBalance={(uid, cur) => setBalanceModal({ isOpen: true, userId: uid, currentBalance: cur })}
            onSendMessage={(uid, uname) => setMessageModal({ isOpen: true, userId: uid, username: uname })}
            onDeleteUser={handleDeleteUser}
          />
        )}

        {activeTab === 'shop' && (
          <ShopTab
            products={products}
            orders={orders}
            onCreateProduct={handleCreateProduct}
            onUpdateProduct={handleUpdateProduct}
            onDeleteProduct={handleDeleteProduct}
            onAddStock={handleAddStock}
          />
        )}

        {activeTab === 'bank' && (
          <BankTab
            transactions={transactions}
            onSyncBank={handleSyncBank}
            isSyncing={isSyncingBank}
          />
        )}

        {activeTab === 'accounts' && (
          <AccountsTab
            accounts={accounts}
            onGenerateAccount={handleGenerateAccount}
            onDeleteAccount={handleDeleteAccount}
            isGenerating={isGenerating}
          />
        )}

        {activeTab === 'broadcast' && (
          <BroadcastTab totalUsers={users.length} onSendBroadcast={handleSendBroadcast} />
        )}
      </main>

      <Modals
        bonusModal={bonusModal}
        onCloseBonus={() => setBonusModal({ isOpen: false, userId: 0, currentBonus: 0 })}
        onSubmitBonus={handleUpdateBonus}
        balanceModal={balanceModal}
        onCloseBalance={() => setBalanceModal({ isOpen: false, userId: 0, currentBalance: 0 })}
        onSubmitBalance={handleUpdateBalance}
        messageModal={messageModal}
        onCloseMessage={() => setMessageModal({ isOpen: false, userId: 0, username: null })}
        onSubmitMessage={handleSendMessage}
      />
    </div>
  );
}

export default App;
