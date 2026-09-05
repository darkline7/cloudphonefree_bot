import React, { useState } from 'react';
import type { AccountItem } from '../types';
import { Search, Download, Trash2, Key, CheckCircle, XCircle, PlusCircle, RefreshCw } from 'lucide-react';


interface AccountsTabProps {
  accounts: AccountItem[];
  onGenerateAccount: () => void;
  onDeleteAccount: (accountId: number) => void;
  isGenerating: boolean;
}

export const AccountsTab: React.FC<AccountsTabProps> = ({
  accounts,
  onGenerateAccount,
  onDeleteAccount,
  isGenerating,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredAccounts = accounts.filter((acc) => {
    const q = searchTerm.toLowerCase();
    return (
      acc.email.toLowerCase().includes(q) ||
      acc.user_id.toString().includes(q) ||
      (acc.username && acc.username.toLowerCase().includes(q)) ||
      (acc.api_user_id && acc.api_user_id.toLowerCase().includes(q))
    );
  });

  const exportToCSV = () => {
    const headers = ['ID', 'Telegram User ID', 'Username', 'Email', 'API User ID', 'Trial 6h', 'Ngay Tao'];
    const rows = filteredAccounts.map((a) => [
      a.id,
      a.user_id,
      a.username || '',
      a.email,
      a.api_user_id || '',
      a.trial_received === 1 ? 'Co' : 'Khong',
      a.created_at,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.map((val) => `"${val}"`).join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `umocloud_accounts_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-emerald-400" />
            Lịch Sử Cấp Tài Khoản ({accounts.length})
          </h2>
          <p className="text-sm text-slate-400">Danh sách tài khoản UmoCloud 6h được hệ thống cấp tự động và thủ công</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm email, user ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-800/80 border border-slate-700/80 text-slate-200 text-sm rounded-xl pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 w-64"
            />
          </div>

                    <button
            onClick={exportToCSV}
            className="px-3.5 py-2 rounded-xl text-xs font-medium bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            Xuất CSV
          </button>

          <button
            disabled={isGenerating}
            onClick={onGenerateAccount}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/20 flex items-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
          >
            {isGenerating ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <PlusCircle className="w-4 h-4" />
            )}
            Tạo Tài Khoản Ngay
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800/80">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-800/60 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-4 py-3.5">ID</th>
              <th className="px-4 py-3.5">Telegram User</th>
              <th className="px-4 py-3.5">Email Đăng Nhập</th>
              <th className="px-4 py-3.5">API User ID</th>
              <th className="px-4 py-3.5 text-center">Gói dùng thử 6h</th>
              <th className="px-4 py-3.5">Thời gian tạo</th>
              <th className="px-4 py-3.5 text-right">Xoá</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredAccounts.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-500">
                  Không có tài khoản nào được tìm thấy.
                </td>
              </tr>
            ) : (
              filteredAccounts.map((acc) => (
                <tr key={acc.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3.5 text-slate-500 font-mono text-xs">#{acc.id}</td>
                  <td className="px-4 py-3.5">
                    <div className="font-mono text-indigo-400 font-semibold">{acc.user_id === 0 ? 'Admin Web' : acc.user_id}</div>
                    <div className="text-xs text-slate-400">{acc.username ? `@${acc.username}` : '-'}</div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="font-mono text-emerald-400 font-medium bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                      {acc.email}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 font-mono text-xs text-slate-400">
                    {acc.api_user_id || '-'}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    {acc.trial_received === 1 ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle className="w-3.5 h-3.5" /> Đã nhận
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                        <XCircle className="w-3.5 h-3.5" /> Chưa nhận
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-xs text-slate-400">{acc.created_at}</td>
                  <td className="px-4 py-3.5 text-right">
                    <button
                      title="Xoá bản ghi"
                      onClick={() => onDeleteAccount(acc.id)}
                      className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-all border border-rose-500/20 cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
