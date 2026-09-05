export interface DashboardStats {
  total_accounts: number;
  total_users: number;
  total_trials: number;
  total_bonus_awarded: number;
  environment: string;
  settings: {
    default_quota: number;
    referral_reward: number;
    required_chat_id: number;
    required_chat_url: string;
  };
}

export interface UserItem {
  user_id: number;
  username: string | null;
  first_name: string | null;
  referrer_id: number | null;
  bonus_turns: number;
  balance: number;
  total_deposited: number;
  created_at: string;
  last_seen_at: string;
}

export interface AccountItem {
  id: number;
  user_id: number;
  username: string | null;
  email: string;
  api_user_id: string | null;
  trial_received: number;
  created_at: string;
}

export interface ProductItem {
  id: number;
  name: string;
  price: number;
  description: string | null;
  is_active: boolean;
  created_at: string | null;
  stock_count: number;
}

export interface ProductStockItem {
  id: number;
  product_id: number;
  data: string;
  is_sold: boolean;
  order_id: number | null;
  created_at: string | null;
}

export interface OrderItem {
  id: number;
  user_id: number;
  username: string | null;
  product_id: number;
  product_name: string;
  price: number;
  account_data: string;
  created_at: string | null;
}

export interface BankTransactionItem {
  id: number;
  transaction_id: string | number;
  amount: number;
  description: string;
  transaction_date: string | null;
  user_id: number | null;
  created_at: string | null;
}

export interface AuthState {
  authenticated: boolean;
  username: string | null;
}

