// Chat Types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatSession {
  sessionId: string | null;
  messages: Message[];
  phase: ConversationPhase;
  isComplete: boolean;
  experts: ExpertRecommendation[] | null;
}

export type ConversationPhase =
  | 'start'
  | 'greeting'
  | 'gathering'
  | 'extracting'
  | 'analyzing'
  | 'matching'
  | 'presenting'
  | 'selecting'
  | 'handoff'
  | 'complete';

// Expert Types
export interface Expert {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  title: string;
  bio?: string;
  years_experience: number;
  skills: string[];
  certifications: string[];
  specializations?: string[];
  hourly_rate?: number;
  currency: string;
  availability: boolean;
  response_time?: string;
  location?: string;
  timezone?: string;
  languages: string[];
  rating: number;
  total_reviews: number;
  total_cases?: number;
  whatsapp?: string;
  linkedin?: string;
  website?: string;
  // External freelancer profiles (listed with a link, not affiliated)
  is_external?: boolean;
  profile_platform?: string;
  profile_url?: string;
}

export interface ExpertMatch {
  expert_id: number;
  match_score: number;
  matched_skills: string[];
  matched_certifications: string[];
  match_reasons: string[];
  path_length?: number;
  location_bonus?: number;
  urgency_bonus?: number;
  availability_bonus?: number;
}

export interface ExpertRecommendation {
  expert: Expert;
  match: ExpertMatch;
  explanation?: string;
  rank?: number;
  contact_options?: string[];
}

// API Response Types
export interface StartChatResponse {
  session_id: string;
  response: string;
  phase: ConversationPhase;
}

export interface ContinueChatResponse {
  session_id: string;
  response: string;
  phase: ConversationPhase;
  is_complete: boolean;
  experts?: ExpertRecommendation[];
}

export interface SelectExpertResponse {
  session_id: string;
  response: string;
  phase: ConversationPhase;
  is_complete: boolean;
}

// API Request Types
export interface ChatRequest {
  message: string;
}
