export type Json = boolean | number | string | null | Json[] | { [key: string]: Json };

export interface Database {
  public: {
    Tables: {
      demo_runs: {
        Row: {
          created_at: string;
          final_report: string;
          id: string;
          is_public: boolean;
          owner_id: string | null;
          panel: Json;
          question: string;
          share_slug: string | null;
          status: "ready" | "running" | "completed" | "failed" | "cancelled";
          updated_at: string;
        };
        Insert: {
          final_report: string;
          is_public?: boolean;
          owner_id?: string | null;
          panel: Json;
          question: string;
          share_slug?: string | null;
          status?: "ready" | "running" | "completed" | "failed" | "cancelled";
        };
        Update: {
          final_report?: string;
          is_public?: boolean;
          panel?: Json;
          question?: string;
          share_slug?: string | null;
          status?: "ready" | "running" | "completed" | "failed" | "cancelled";
        };
      };
      panel_presets: {
        Row: {
          created_at: string;
          id: string;
          is_public: boolean;
          name: string;
          owner_id: string;
          panel: Json;
          updated_at: string;
        };
        Insert: {
          is_public?: boolean;
          name: string;
          owner_id: string;
          panel: Json;
        };
        Update: {
          is_public?: boolean;
          name?: string;
          panel?: Json;
        };
      };
      profiles: {
        Row: {
          created_at: string;
          display_name: string | null;
          id: string;
          updated_at: string;
        };
        Insert: {
          display_name?: string | null;
          id: string;
        };
        Update: {
          display_name?: string | null;
        };
      };
      run_events: {
        Row: {
          created_at: string;
          detail: string;
          id: number;
          phase: "build" | "critique" | "debate" | "judge" | "final";
          progress: number;
          run_id: string;
          status: "ready" | "running" | "completed" | "failed" | "cancelled";
          title: string;
        };
        Insert: {
          detail: string;
          phase: "build" | "critique" | "debate" | "judge" | "final";
          progress: number;
          run_id: string;
          status: "ready" | "running" | "completed" | "failed" | "cancelled";
          title: string;
        };
        Update: never;
      };
    };
  };
}
