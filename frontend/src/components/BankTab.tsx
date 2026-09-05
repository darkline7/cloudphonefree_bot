import { useState } from 'react';
import type { BankTransactionItem } from '../types';
import { Landmark, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

interface Props {
  transactions: BankTransactionItem[];
  onSyncBank: () => Promise<void>;
  isSyncing: boolean;
}

export function BankTab({ transactions, onSyncBank, isSyncing }: Props) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = transactions.filter((t) => {
    const term = searchTerm.toLowerCase();
    return (
      t.transaction_id.toString().includes(term) ||
      t.description.toLowerCase().includes(term) ||
      (t.user_id && t.user_id.toString().includes(term))
    );
  });

  const totalAmount = transactions.reduce((acc, t) => acc + t.amount, 0);

  return (
    <div className="space-y-6">
      {/* Header & Stats */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Landmark className="w-5 h-5 text-indigo-400" />
            Lịch Sử Giao Dịch Nạp Tiền Ngân Hàng (Auto ACB)
          </h2>
          <p className="text-sm text-slate-400">
            Tự động kiểm tra và cộng số dư theo cú pháp <code className="text-amber-300">NAP &lt;user_id&gt;</code>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl px-4 py-2 text-sm">
            <span className="text-slate-400">Tổng đã nạp: </span>
            <span className="font-bold font-mono text-emerald-400">{totalAmount.toLocaleString()}đ</span>
          </div>

          <button
            onClick={onSyncBank}
            disabled={isSyncing}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            Đồng Bộ ACB Ngay
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 backdrop-blur-xl">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Tìm theo Mã Giao Dịch, ID User, Nội Dung..."
          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
        />
      </div>

      {/* Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950/60 text-xs uppercase text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Mã GD (ACB)</th>
                <th className="px-6 py-4">Số Tiền</th>
                <th className="px-6 py-4">User Telegram</th>
                <th className="px-6 py-4">Nội Dung Chuyển Khoản</th>
                <th className="px-6 py-4">Thời Gian GD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/30 transition">
                  <td className="px-6 py-4 font-mono font-bold text-indigo-400">#{t.transaction_id}</td>
                  <td className="px-6 py-4 font-mono font-bold text-emerald-400">
                    +{t.amount.toLocaleString()}đ
                  </td>
                  <td className="px-6 py-4">
                    {t.user_id ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        <CheckCircle2 className="w-3 h-3 text-indigo-400" />
                        ID: {t.user_id}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400">
                        <AlertCircle className="w-3 h-3" />
                        Chưa gán User
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <code className="bg-slate-950 px-2.5 py-1 rounded-md text-xs font-mono text-slate-300 border border-slate-800">
                      {t.description}
                    </code>
                  </td>
                  <td className="px-6 py-4 text-xs text-slate-400">
                    {t.transaction_date || t.created_at || 'Vừa xong'}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    Chưa có giao dịch ngân hàng nào được ghi nhận.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
