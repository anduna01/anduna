export type Growth = {
  snapshots: number;
  sufficient_data: boolean;
  views_per_hour_recent: number | null;
  views_per_hour_overall: number | null;
  view_delta: number | null;
  hours_span: number | null;
};

export type Tag = { id: number; name: string };

export type Reference = {
  id: number;
  source: "youtube" | "manual";
  youtube_id: string | null;
  title: string;
  channel_title: string | null;
  url: string;
  thumbnail_url: string | null;
  published_at: string | null;
  duration_seconds: number | null;
  description: string | null;
  language: string | null;
  region: string | null;
  category: string | null;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  last_fetched_at: string | null;
  is_favorite: boolean;
  notes: string | null;
  status: string;
  created_at: string;
  tags: Tag[];
  growth: Growth | null;
};

export type RadarVideo = {
  youtube_id: string;
  url: string;
  title: string;
  channel_title: string | null;
  published_at: string | null;
  duration_seconds: number | null;
  thumbnail_url: string | null;
  language: string | null;
  category_id: string | null;
  view_count: number | null;
  like_count: number | null;
  comment_count: number | null;
  avg_views_per_day: number | null;
  growth: Growth;
  reference_id: number | null;
};

export type RadarResult = {
  videos: RadarVideo[];
  next_page_token: string | null;
  total_results: number | null;
  filtered_out: number;
};

export type Category = { id: string; title: string };
