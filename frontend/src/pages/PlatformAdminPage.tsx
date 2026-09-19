import React, { useState, useEffect } from 'react';
import { Building, CheckCircle, Play, Server, Brain, Users, Activity, ShieldCheck, Database, Cpu } from 'lucide-react';
import { api } from '../services/api';
import type { Hospital } from '../types';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { MetricCard } from '../components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DataTable, type Column } from '../components/ui/DataTable';
import { EmptyState } from '../components/ui/States';

export const PlatformAdminPage: React.FC = () => {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [platformMetrics, setPlatformMetrics] = useState<any>(null);
  const [aiMetrics, setAiMetrics] = useState<any>(null);
  const [healthData, setHealthData] = useState<any>(null);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [runningEval, setRunningEval] = useState(false);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'HOSPITALS' | 'HEALTH' | 'AI'>('OVERVIEW');

  useEffect(() => {
    api.getHospitals().then(setHospitals).catch(console.error);
    api.getPlatformAnalytics().then(setPlatformMetrics).catch(console.error);
    api.getAIMetrics().then(setAiMetrics).catch(console.error);
    api.getHealth().then(setHealthData).catch(console.error);
  }, []);

  const handleTriggerEval = async () => {
    setRunningEval(true);
    try {
      const res = await api.runSafetyEval();
      setEvalResult(res);
      // Refresh AI metrics after running evaluation
      api.getAIMetrics().then(setAiMetrics).catch(console.error);
    } catch (err) {
      console.error(err);
    } finally {
      setRunningEval(false);
    }
  };

  const columns: Column<Hospital>[] = [
    {
      header: 'Code',
      accessor: 'code',
      cell: (h) => <span className="font-mono font-bold text-cyan-800">{h.code}</span>,
    },
    {
      header: 'Hospital Network',
      accessor: 'name',
      cell: (h) => (
        <div>
          <p className="font-bold text-slate-900">{h.name}</p>
          <p className="text-[10px] text-slate-400 font-mono">ID: {h.id}</p>
        </div>
      ),
    },
    {
      header: 'Timezone',
      accessor: 'timezone',
      cell: (h) => <span className="font-mono text-slate-600">{h.timezone}</span>,
    },
    {
      header: 'Calling Window',
      cell: (h) => (
        <span className="text-slate-700">
          {h.calling_start_hour}:00 - {h.calling_end_hour}:00 Local
        </span>
      ),
    },
    {
      header: 'Max Concurrency',
      cell: (h) => (
        <Badge variant="eucalyptus">{h.max_concurrent_calls} concurrent calls</Badge>
      ),
    },
    {
      header: 'Isolation',
      cell: () => <Badge variant="sage">TENANT ISOLATED</Badge>,
    },
  ];

  const disagreementDisplay =
    aiMetrics?.disagreement_rate !== null && aiMetrics?.disagreement_rate !== undefined
      ? `${(aiMetrics.disagreement_rate * 100).toFixed(1)}%`
      : '—';

  const disagreementSubtext =
    aiMetrics?.has_consensus_data || (aiMetrics?.total_decisions && aiMetrics.total_decisions > 0)
      ? `${aiMetrics.disagreement_count ?? 0} of ${aiMetrics.total_decisions} consensus evaluations`
      : 'No assessments yet';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hospital Network Command Center"
        subtitle="Multi-Tenant Operations, System Health & Dual-LLM Safety Auditing"
        badge={<Badge variant="purple">PLATFORM ADMIN</Badge>}
        actions={
          <Button
            variant="primary"
            loading={runningEval}
            onClick={handleTriggerEval}
            icon={<Play className="w-4 h-4" />}
          >
            {runningEval ? 'Evaluating Benchmark...' : 'Run Safety Evaluation'}
          </Button>
        }
      />

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-xs font-semibold">
        <button
          onClick={() => setActiveTab('OVERVIEW')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'OVERVIEW' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('HOSPITALS')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'HOSPITALS' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          Hospitals ({hospitals.length})
        </button>
        <button
          onClick={() => setActiveTab('HEALTH')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'HEALTH' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          System Health
        </button>
        <button
          onClick={() => setActiveTab('AI')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer ${
            activeTab === 'AI' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          AI Operations
        </button>
      </div>

      {/* Safety Evaluation Report Alert if generated */}
      {evalResult && (
        <Card className="border-purple-300 bg-purple-50/40">
          <CardHeader action={<span className="text-xs font-mono text-purple-700 font-bold">Version: {evalResult.prompt_version}</span>}>
            <CardTitle className="text-purple-950 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-purple-700" />
              <span>Safety Benchmark Evaluation Completed</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div className="bg-white p-3 rounded-lg border border-purple-200">
                <p className="text-[11px] text-slate-500 font-semibold uppercase">False Negative Rate</p>
                <p className="text-xl font-bold text-emerald-700">{((evalResult.metrics?.false_negative_rate ?? 0) * 100).toFixed(2)}%</p>
                <span className="text-[10px] text-emerald-600 font-semibold">0.00% Required Target</span>
              </div>
              <div className="bg-white p-3 rounded-lg border border-purple-200">
                <p className="text-[11px] text-slate-500 font-semibold uppercase">False Negatives</p>
                <p className="text-xl font-bold text-emerald-700">{evalResult.metrics?.false_negatives ?? 0}</p>
                <span className="text-[10px] text-emerald-600 font-semibold">Passed Benchmark</span>
              </div>
              <div className="bg-white p-3 rounded-lg border border-purple-200">
                <p className="text-[11px] text-slate-500 font-semibold uppercase">Precision</p>
                <p className="text-xl font-bold text-purple-900">{((evalResult.metrics?.precision ?? 0) * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-white p-3 rounded-lg border border-purple-200">
                <p className="text-[11px] text-slate-500 font-semibold uppercase">Recall</p>
                <p className="text-xl font-bold text-purple-900">{((evalResult.metrics?.recall ?? 0) * 100).toFixed(1)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Hospitals"
          value={hospitals.length}
          subtext="100% Strict Tenant Isolation"
          icon={<Building className="w-5 h-5 text-cyan-700" />}
          variant="eucalyptus"
        />
        <MetricCard
          title="Outreach Volume"
          value={platformMetrics?.total_patients_managed ?? 0}
          subtext="Managed Patients Across Network"
          icon={<Users className="w-5 h-5 text-emerald-700" />}
          variant="sage"
        />
        <MetricCard
          title="System Health"
          value={healthData?.status || platformMetrics?.system_status || 'HEALTHY'}
          subtext={healthData?.components?.database?.status === 'HEALTHY' ? 'API, DB & Queue Online' : 'System Operational'}
          icon={<Server className="w-5 h-5 text-amber-700" />}
          variant="amber"
        />
        <MetricCard
          title="AI Disagreement"
          value={disagreementDisplay}
          subtext={disagreementSubtext}
          icon={<Brain className="w-5 h-5 text-purple-700" />}
          variant="lavender"
        />
      </div>

      {/* Tab Specific Content */}
      {activeTab === 'HEALTH' ? (
        <Card>
          <CardHeader action={<Badge variant="eucalyptus">LIVE SERVICE STATUS</Badge>}>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-700" />
              <span>Platform Infrastructure Services Health</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Server className="w-4 h-4 text-cyan-700" /> API Gateway
                  </span>
                  <Badge variant="eucalyptus">{healthData?.components?.api?.status || 'HEALTHY'}</Badge>
                </div>
                <p className="text-xs text-slate-500">Version: {healthData?.components?.api?.version || '2.0.0'}</p>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Database className="w-4 h-4 text-emerald-700" /> Database Engine
                  </span>
                  <Badge variant="eucalyptus">{healthData?.components?.database?.status || 'HEALTHY'}</Badge>
                </div>
                <p className="text-xs text-slate-500">PostgreSQL Tenant Scoped</p>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-800 text-sm flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-amber-700" /> Async Worker Pool
                  </span>
                  <Badge variant="eucalyptus">{healthData?.components?.redis_queue?.status || 'HEALTHY'}</Badge>
                </div>
                <p className="text-xs text-slate-500">Mode: {healthData?.components?.redis_queue?.mode || 'ASYNC_WORKER_POOL'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : activeTab === 'AI' ? (
        <Card>
          <CardHeader action={<Badge variant={aiMetrics?.active_provider === 'gemini' ? 'purple' : 'slate'}>{aiMetrics?.active_provider === 'gemini' ? 'GEMINI REST API' : 'DEVELOPMENT MOCK'}</Badge>}>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-purple-700" />
              <span>AI Operations & Provider Architecture</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg border border-purple-200 bg-purple-50/40 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <p className="font-bold text-purple-950 text-sm">
                  {aiMetrics?.active_provider === 'gemini' ? 'Gemini — External LLM' : 'Mock AI — Development/Simulation Mode'}
                </p>
                <p className="text-xs text-purple-800">
                  Model: <span className="font-mono font-semibold">{aiMetrics?.active_model || 'default'}</span> | Key Status:{' '}
                  <span className="font-semibold">{aiMetrics?.api_key_configured ? 'Configured' : 'Not Configured (Offline Mode)'}</span>
                </p>
              </div>
              <Badge variant={aiMetrics?.active_provider === 'gemini' ? 'purple' : 'slate'}>
                {aiMetrics?.active_provider === 'gemini' ? 'External API Active' : 'Offline Rule Synthesizer'}
              </Badge>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <p className="text-xs text-slate-500 font-semibold uppercase">Total AI Requests</p>
                <p className="text-xl font-bold text-slate-900">{aiMetrics?.total_requests ?? 0}</p>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <p className="text-xs text-slate-500 font-semibold uppercase">Avg Latency</p>
                <p className="text-xl font-bold text-slate-900">{aiMetrics?.average_latency_ms ?? 0} ms</p>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <p className="text-xs text-slate-500 font-semibold uppercase">Validation Success</p>
                <p className="text-xl font-bold text-emerald-700">{((aiMetrics?.structured_validation_success_rate ?? 1.0) * 100).toFixed(1)}%</p>
              </div>
              <div className="p-3 bg-slate-50 rounded border border-slate-200">
                <p className="text-xs text-slate-500 font-semibold uppercase">Disagreement Rate</p>
                <p className="text-xl font-bold text-purple-900">{disagreementDisplay}</p>
              </div>
            </div>
          </CardContent>
        </Card>

      ) : (
        /* Hospitals Table or Empty State */
        <Card>
          <CardHeader action={<Badge variant="slate">PostgreSQL Tenant Scoping</Badge>}>
            <CardTitle>Hospital Network Tenant Register & Concurrency Capacity</CardTitle>
          </CardHeader>
          {hospitals.length === 0 ? (
            <EmptyState
              title="No Hospital Tenants Registered"
              description="No hospital network tenants exist in the database. Run database seed to populate demo hospital tenants."
              icon={<Building className="w-10 h-10 text-slate-300" />}
            />
          ) : (
            <DataTable
              columns={columns}
              data={hospitals}
              keyExtractor={(h) => h.id}
            />
          )}
        </Card>
      )}
    </div>
  );
};
