export interface PulseUpdateEvent {
  event: 'PULSE_UPDATE';
  stock_id: number;
  previous_score: number;
  current_score: number;
  severity: string;
  momentum: number;
}

export interface NotificationEvent {
  event: 'NOTIFICATION';
  stock: string;
  severity: string;
  title: string;
  message: string;
}
