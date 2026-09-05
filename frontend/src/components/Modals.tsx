import React, { useState } from 'react';
import { Gift, MessageSquare, Wallet, X } from 'lucide-react';

interface ModalsProps {
  bonusModal: { isOpen: boolean; userId: number; currentBonus: number };
  onCloseBonus: () => void;
  onSubmitBonus: (userId: number, bonusTurns: number) => void;
  balanceModal: { isOpen: boolean; userId: number; currentBalance: number };
  onCloseBalance: () => void;
  onSubmitBalance: (userId: number, balance: number) => void;
  messageModal: { isOpen: boolean; userId: number; username: string | null };
  onCloseMessage: () => void;
  onSubmitMessage: (userId: number, content: string) => Promise<boolean>;
}

export const Modals: React.FC<ModalsProps> = ({
  bonusModal,
  onCloseBonus,
  onSubmitBonus,
  balanceModal,
  onCloseBalance,
  onSubmitBalance,
  messageModal,
  onCloseMessage,
  onSubmitMessage,
}) => {
  const [bonusInput, setBonusInput] = useState(bonusModal.currentBonus);
  const [balanceInput, setBalanceInput] = useState(balanceModal.currentBalance);
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  React.useEffect(() => {
    setBonusInput(bonusModal.currentBonus);
  }, [bonusModal.currentBonus]);

  React.useEffect(() => {
    setBalanceInput(balanceModal.currentBalance);
  }, [balanceModal.currentBalance]);

  return (
    <>
      {bonusModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Gift className="w-5 h-5 text-amber-400" />
                Cập Nhật Lượt Thưởng
              </h3>
              <button
                onClick={onCloseBonus}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-4">
              Chỉnh sửa số lượt thưởng thêm cho User ID:{' '}
              <code className="text-amber-400 font-bold">{bonusModal.userId}</code>. Tổng hạn mức sẽ là{' '}
              <b>10 (mặc định) + lượt thưởng</b>.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Lượt Thưởng Thêm (Bonus Turns)
                </label>
                <input
                  type="number"
                  min={0}
                  value={bonusInput}
                  onChange={(e) => setBonusInput(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                />
              </div>

              <div className="flex items-center gap-2">
                {[5, 10, 20, 50].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setBonusInput(bonusInput + num)}
                    className="flex-1 py-1.5 rounded-lg text-xs font-medium bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white cursor-pointer"
                  >
                    +{num}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={onCloseBonus}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
                >
                  Huỷ
                </button>
                <button
                  type="button"
                  onClick={() => onSubmitBonus(bonusModal.userId, bonusInput)}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/20 cursor-pointer"
                >
                  Lưu Thay Đổi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {balanceModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Wallet className="w-5 h-5 text-emerald-400" />
                Cập Nhật Số Dư Ví
              </h3>
              <button
                onClick={onCloseBalance}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-4">
              Cập nhật số dư trong ví cho User ID:{' '}
              <code className="text-emerald-400 font-bold">{balanceModal.userId}</code>.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Số Dư Ví (VNĐ)
                </label>
                <input
                  type="number"
                  min={0}
                  step={1000}
                  value={balanceInput}
                  onChange={(e) => setBalanceInput(Math.max(0, parseInt(e.target.value) || 0))}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-2.5 text-lg font-bold focus:outline-none focus:ring-2 focus:ring-emerald-500/50 font-mono"
                />
              </div>

              <div className="flex items-center gap-2">
                {[10000, 20000, 50000, 100000].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setBalanceInput(balanceInput + num)}
                    className="flex-1 py-1.5 rounded-lg text-xs font-medium bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white cursor-pointer font-mono"
                  >
                    +{num / 1000}k
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={onCloseBalance}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
                >
                  Huỷ
                </button>
                <button
                  type="button"
                  onClick={() => onSubmitBalance(balanceModal.userId, balanceInput)}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-500/20 cursor-pointer"
                >
                  Lưu Số Dư
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {messageModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-400" />
                Gửi Tin Nhắn Riêng
              </h3>
              <button
                onClick={onCloseMessage}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-4">
              Gửi tin nhắn trực tiếp qua Telegram Bot tới người dùng{' '}
              <code className="text-blue-400 font-bold">{messageModal.userId}</code>
              {messageModal.username ? ` (@${messageModal.username})` : ''}.
            </p>

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                if (!messageInput.trim()) return;
                setIsSending(true);
                const ok = await onSubmitMessage(messageModal.userId, messageInput);
                setIsSending(false);
                if (ok) {
                  setMessageInput('');
                  onCloseMessage();
                }
              }}
              className="space-y-4"
            >
              <div>
                <textarea
                  rows={5}
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder="Nhập nội dung tin nhắn gửi riêng..."
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl p-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={onCloseMessage}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
                >
                  Huỷ
                </button>
                <button
                  type="submit"
                  disabled={isSending}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/20 disabled:opacity-50 cursor-pointer"
                >
                  {isSending ? 'Đang gửi...' : 'Gửi Tin Nhắn'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

