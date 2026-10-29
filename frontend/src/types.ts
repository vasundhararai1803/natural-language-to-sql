export interface MetricCard {
  label: string;
  value: string | number;
  change_pct?: number;
  comparison_label?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
}

export interface ContributingFactor {
  dimension: string;
  segment: string;
  baseline_value: number;
  current_value: number;
  delta: number;
  percentage_change: number;
  contribution_to_total_drop_pct: number;
  is_anomaly: boolean;
  note?: string;
}

export interface ChartSeries {
  data_key: string;
  name: string;
  color?: string;
}

export interface ChartSpec {
  chart_type: 'line' | 'bar' | 'grouped_bar' | 'pie' | 'table';
  title: string;
  x_axis_key?: string;
  y_axis_key?: string;
  series: ChartSeries[];
  x_label?: string;
  y_label?: string;
  unit?: string;
  highlight_anomalies?: boolean;
}

export interface QueryResponse {
  request_id: string;
  question: string;
  interpreted_intent: Record<string, any>;
  clarification_required: boolean;
  clarification_message?: string;
  assumptions: string[];
  sql: string;
  query_status: 'success' | 'error' | 'rejected' | 'clarification';
  execution_time_ms: number;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  metric_cards: MetricCard[];
  chart_spec?: ChartSpec;
  summary: string;
  key_findings: string[];
  contributing_factors: ContributingFactor[];
  data_quality_warnings: string[];
  limitations: string[];
  execution_mode: string;
  follow_up_questions: string[];
  confidence_score: number;
  confidence_reasoning: string;
}

export interface SchemaColumn {
  name: string;
  type: string;
  primary_key: boolean;
  foreign_key?: string;
  description: string;
}

export interface SchemaTable {
  table_name: string;
  description: string;
  columns: SchemaColumn[];
}

export interface MetricDefinition {
  metric_id: string;
  name: string;
  formula: string;
  business_meaning: string;
  default_table: string;
  default_filter?: string;
}

export interface BenchmarkResultItem {
  test_id: string;
  question: string;
  difficulty: string;
  category: string;
  passed: boolean;
  execution_status: string;
  safety_check_passed: boolean;
  result_correctness: boolean;
  semantic_correctness: boolean;
  insight_faithfulness: boolean;
  latency_ms: number;
  generated_sql?: string;
  failure_reason?: string;
}

export interface BenchmarkSummary {
  total_tests: number;
  passed_tests: number;
  overall_accuracy_pct: number;
  execution_accuracy_pct: number;
  result_correctness_pct: number;
  semantic_correctness_pct: number;
  sql_safety_rate_pct: number;
  insight_faithfulness_pct: number;
  average_latency_ms: number;
  execution_mode: string;
  timestamp: string;
  results: BenchmarkResultItem[];
}
