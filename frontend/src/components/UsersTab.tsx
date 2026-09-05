import React, { useState } from 'react';
import type { UserItem } from '../types';
import { Search, Gift, MessageSquare, Trash2, ArrowUpDown, UserCheck, Sparkles, Wallet } from 'lucide-react';

interface UsersTabProps {
  users: UserItem[];
  onUpdateBonus: (userId: number, currentBonus: number) => void;
  onUpdateBalance: (userId: number, currentBalance: number) => void;
  onSendMessage: (userId: number, username: string | null) => void;
  onDeleteUser: (userId: number) => void;
}

export const UsersTab: React.FC<UsersTabProps> = ({
  users,
  onUpdateBonus,
  onUpdateBalance,
  onSendMessage,
  onDeleteUser,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<'created_at' | 'bonus_turns' | 'balance'>('created_at');
  const [sortAsc, setSortAsc] = useState(false);

  const filteredUsers = users
    .filter((u) => {
      const q = searchTerm.toLowerCase();
      return (
        u.user_id.toString().includes(q) ||
        (u.username && u.username.toLowerCase().includes(q)) ||
        (u.first_name && u.first_name.toLowerCase().includes(q)) ||
        (u.referrer_id && u.referrer_id.toString().includes(q))
      );
    })
    .sort((a, b) => {
      if (sortField === 'bonus_turns') {
        return sortAsc ? a.bonus_turns - b.bonus_turns : b.bonus_turns - a.bonus_turns;
      }
      if (sortField === 'balance') {
        return sortAsc ? (a.balance || 0) - (b.balance || 0) : (b.balance || 0) - (a.balance || 0);
      }
      return sortAsc
        ? new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        : new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  return (
    <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-indigo-400" />
            Danh Sách Người Dùng ({users.length})
          </h2>
          <p className="text-sm text-slate-400">Quản lý Telegram ID, số dư ví, phân phối lượt thưởng và tương tác trực tiếp</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Tìm user ID, username..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-800/80 border border-slate-700/80 text-slate-200 text-sm rounded-xl pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 w-64"
            />
          </div>

          <button
            onClick={() => {
              if (sortField === 'balance') {
                setSortAsc(!sortAsc);
              } else {
                setSortField('balance');
                setSortAsc(false);
              }
            }}
            className={
              'px-3 py-2 rounded-xl text-xs font-medium border flex items-center gap-1.5 transition-all cursor-pointer ' +
              (sortField === 'balance'
                ? 'bg-emerald-600/20 border-emerald-500 text-emerald-300'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700')
            }
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            Xếp theo Số Dư Ví
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800/80">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-800/60 text-xs uppercase font-semibold text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-4 py-3.5">Telegram User</th>
              <th className="px-4 py-3.5">Tên / Username</th>
              <th className="px-4 py-3.5">Số Dư Ví</th>
              <th className="px-4 py-3.5">Người giới thiệu</th>
              <th className="px-4 py-3.5 text-center">Hạn mức khả dụng</th>
              <th className="px-4 py-3.5">Thời gian tham gia</th>
              <th className="px-4 py-3.5 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {filteredUsers.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-10 text-slate-500">
                  Không tìm thấy người dùng phù hợp.
                </td>
              </tr>
            ) : (
              filteredUsers.map((u) => (
                <tr key={u.user_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3.5 font-mono text-indigo-400 font-semibold">
                    <code>{u.user_id}</code>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="font-medium text-white">{u.first_name || 'Khách'}</div>
                    <div className="text-xs text-slate-400">@{u.username || 'không có'}</div>
                  </td>
                  <td className="px-4 py-3.5 font-mono font-bold text-emerald-400">
                    {(u.balance || 0).toLocaleString()}đ
                  </td>
                  <td className="px-4 py-3.5">
                    {u.referrer_id ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 font-mono border border-slate-700">
                        {u.referrer_id}
                      </span>
                    ) : (
                      <span className="text-slate-500 text-xs">Trực tiếp</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      <Sparkles className="w-3 h-3 text-indigo-400" />
                      {10 + u.bonus_turns} lượt ({u.bonus_turns > 0 ? `+${u.bonus_turns} bonus` : 'mặc định 10'})
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-xs text-slate-400">
                    <div>{u.created_at}</div>
                    <div className="text-[11px] text-slate-500">Online: {u.last_seen_at}</div>
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        title="Chỉnh sửa số dư ví"
                        onClick={() => onUpdateBalance(u.user_id, u.balance || 0)}
                        className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-all border border-emerald-500/20 cursor-pointer"
                      >
                        <Wallet className="w-4 h-4" />
                      </button>

                      <button
                        title="Chỉnh sửa lượt thưởng"
                        onClick={() => onUpdateBonus(u.user_id, u.bonus_turns)}
                        className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 transition-all border border-amber-500/20 cursor-pointer"
                      >
                        <Gift className="w-4 h-4" />
                      </button>

                      <button
                        title="Gửi tin nhắn riêng"
                        onClick={() => onSendMessage(u.user_id, u.username)}
                        className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-all border border-blue-500/20 cursor-pointer"
                      >
                        <MessageSquare className="w-4 h-4" />
                      </button>

                      <button
                        title="Xoá người dùng"
                        onClick={() => onDeleteUser(u.user_id)}
                        className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-all border border-rose-500/20 cursor-pointer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
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
