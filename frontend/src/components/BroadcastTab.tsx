import React, { useState } from 'react';
import { Megaphone, Send, Users, ShieldAlert, Sparkles, CheckCircle2 } from 'lucide-react';

interface BroadcastTabProps {
  totalUsers: number;
  onSendBroadcast: (content: string, targetUserId?: number) => Promise<boolean>;
}

export const BroadcastTab: React.FC<BroadcastTabProps> = ({ totalUsers, onSendBroadcast }) => {
  const [content, setContent] = useState('');
  const [targetUserId, setTargetUserId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIsSubmitting(true);
    setSuccessMsg('');
    const target = targetUserId.trim() ? parseInt(targetUserId.trim(), 10) : undefined;
    const ok = await onSendBroadcast(content, isNaN(Number(target)) ? undefined : target);
    setIsSubmitting(false);

    if (ok) {
      setContent('');
      setTargetUserId('');
      setSuccessMsg('✅ Đã gửi lệnh phát sóng thông báo thành công đến hệ thống!');
      setTimeout(() => setSuccessMsg(''), 6000);
    }
  };

  const insertTemplate = (text: string) => {
    setContent((prev) => (prev ? `${prev}\n${text}` : text));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
        <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
          <Megaphone className="w-5 h-5 text-amber-400" />
          Phát Sóng Thông Báo Telegram
        </h2>
        <p className="text-sm text-slate-400 mb-6">
          Tin nhắn sẽ được gửi tự động qua Bot Telegram tới từng người dùng đã tương tác.
        </p>

        {successMsg && (
          <div className="mb-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Đối tượng nhận tin (Để trống để gửi TẤT CẢ {totalUsers} người dùng)
            </label>
            <div className="relative">
              <Users className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="number"
                placeholder="Nhập User ID cụ thể (Tùy chọn)..."
                value={targetUserId}
                onChange={(e) => setTargetUserId(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700/80 text-slate-200 text-sm rounded-xl pl-10 pr-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Nội dung thông báo (Hỗ trợ HTML: &lt;b&gt;, &lt;i&gt;, &lt;code&gt;)
            </label>
            <textarea
              rows={5}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Nhập nội dung cập nhật, thông báo bảo trì, quà tặng lượt tạo..."
              className="w-full bg-slate-800/80 border border-slate-700/80 text-slate-200 text-sm rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 font-sans"
              required
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => insertTemplate('🎁 <b>TẶNG LƯỢT TẠO MIỄN PHÍ:</b> Mời bạn bè nhận ngay +5 lượt!')}
                className="px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 cursor-pointer"
              >
                Mẫu Quà tặng
              </button>
              <button
                type="button"
                onClick={() => insertTemplate('⚠️ <b>THÔNG BÁO BẢO TRÌ:</b> Hệ thống sẽ nâng cấp trong 30 phút tới.')}
                className="px-2.5 py-1 rounded-lg text-xs bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 cursor-pointer"
              >
                Mẫu Bảo trì
              </button>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white shadow-lg shadow-amber-500/20 flex items-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-4 h-4" />
              {isSubmitting ? 'Đang gửi...' : 'Gửi Thông Báo Ngay'}
            </button>
          </div>
        </form>
      </div>

      <div className="space-y-6">
        <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            Quy Tắc Quota Mới
          </h3>
          <ul className="space-y-3 text-xs text-slate-300">
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
              <span>Mỗi người dùng mới được tạo <b>10 tài khoản mặc định</b>.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
              <span>Người giới thiệu nhận ngay <b>+5 lượt thưởng</b> khi bạn bè tạo account đầu tiên.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
              <span>Không giới hạn số lượt thưởng tích lũy qua link ref.</span>
            </li>
          </ul>
        </div>

        <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 p-6 shadow-xl">
          <h3 className="text-base font-bold text-white flex items-center gap-2 mb-3">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            Lưu Ý Quản Trị
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Broadcast sẽ gửi tin nhắn tuần tự (rate limit 50ms/người) để tránh vi phạm chính sách Spam của Telegram Bot API. Vui lòng không spam nội dung lặp lại.
          </p>
        </div>
      </div>
    </div>
  );
};
