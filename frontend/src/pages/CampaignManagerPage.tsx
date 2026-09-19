import React, { useState, useEffect } from 'react';
import { Play, RefreshCw, AlertTriangle, PhoneCall, Activity, Clock, ShieldAlert, Plus, Pause, CheckCircle, Calendar, BarChart2, Users, ArrowUpRight, Megaphone } from 'lucide-react';
import { api } from '../services/api';
import type { Campaign, OutreachTask, QueueSummary } from '../types';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { MetricCard } from '../components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { DataTable, type Column } from '../components/ui/DataTable';
import { Modal } from '../components/ui/Modal';
import { EmptyState } from '../components/ui/States';

export const CampaignManagerPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [tasks, setTasks] = useState<OutreachTask[]>([]);
  const [summary, setSummary] = useState<QueueSummary | null>(null);
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [stepMessage, setStepMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'QUEUE' | 'CAMPAIGNS' | 'CALLBACKS' | 'RETRIES' | 'ANALYTICS'>('QUEUE');

  // Modal states
  const [isCreateCampaignOpen, setIsCreateCampaignOpen] = useState(false);
  const [isScheduleCallbackOpen, setIsScheduleCallbackOpen] = useState(false);
  const [selectedTaskForCallback, setSelectedTaskForCallback] = useState<string>('');
  const [callbackTimeInput, setCallbackTimeInput] = useState<string>('');

  // New Campaign Form state
  const [newCampaignName, setNewCampaignName] = useState('');
  const [newCampaignPriority, setNewCampaignPriority] = useState(8);
  const [newCampaignConcurrency, setNewCampaignConcurrency] = useState(5);
  const [newCampaignFollowUpHours, setNewCampaignFollowUpHours] = useState(48);

  const reloadData = async () => {
    try {
      const [cRes, tRes, qRes, aRes] = await Promise.all([
        api.getCampaigns(),
        api.getQueueTasks(),
        api.getQueueSummary(),
        api.getHospitalAnalytics()
      ]);
      setCampaigns(cRes);
      setTasks(tRes);
      setSummary(qRes);
      setAnalytics(aRes);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    reloadData();
    const timer = setInterval(reloadData, 5000);
    return () => clearInterval(timer);
  }, []);

  const handleSimulateStep = async (outcome?: string) => {
    setLoading(true);
    setStepMessage(null);
    try {
      const res = await api.simulateQueueStep(outcome);
      setStepMessage(`Queue Step Executed: Task ${res.reserved_task_id ?? ''} -> Outcome: ${res.outcome ?? 'No Work'} | New State: ${res.new_task_state ?? 'N/A'}`);
      await reloadData();
    } catch (err: any) {
      setStepMessage(`Step Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateUrgentCall = async () => {
    setLoading(true);
    try {
      const pendingTask = tasks.find(t => t.state === 'PENDING' || t.state === 'RETRY_SCHEDULED') || tasks[0];
      if (pendingTask) {
        const res = await api.simulateCall(
          pendingTask.id,
          'ESCALATED',
          ["I am experiencing severe chest tightness and I can't catch my breath at all."]
        );
        setStepMessage(`Simulated Urgent Call for Patient ${pendingTask.patient_name || pendingTask.patient_id} -> Consensus: ${res.triage_classification} (Escalated: ${res.escalation_created})`);
        await reloadData();
      } else {
        alert("No tasks currently available in queue to simulate call.");
      }
    } catch (err: any) {
      setStepMessage(`Call Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createCampaign({
        name: newCampaignName,
        priority_score: newCampaignPriority,
        max_concurrent_calls: newCampaignConcurrency,
        follow_up_window_hours: newCampaignFollowUpHours,
        calling_start_hour: 8,
        calling_end_hour: 20
      });
      setStepMessage(`Campaign "${newCampaignName}" created successfully.`);
      setIsCreateCampaignOpen(false);
      setNewCampaignName('');
      await reloadData();
    } catch (err: any) {
      alert(`Create Campaign failed: ${err.message}`);
    }
  };

  const handleStatusChange = async (campaignId: string, status: string) => {
    try {
      await api.updateCampaignStatus(campaignId, status);
      setStepMessage(`Campaign status updated to ${status}`);
      await reloadData();
    } catch (err: any) {
      alert(`Status update failed: ${err.message}`);
    }
  };

  const handleScheduleCallback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTaskForCallback || !callbackTimeInput) return;
    try {
      await api.scheduleCallback(selectedTaskForCallback, new Date(callbackTimeInput).toISOString());
      setStepMessage(`Callback scheduled successfully.`);
      setIsScheduleCallbackOpen(false);
      setSelectedTaskForCallback('');
      setCallbackTimeInput('');
      await reloadData();
    } catch (err: any) {
      alert(`Schedule callback failed: ${err.message}`);
    }
  };

  const activeCampaignName = campaigns.length > 0 ? campaigns[0].name : 'No Active Campaign';

  const queueColumns: Column<OutreachTask>[] = [
    {
      header: 'Priority',
      accessor: 'priority_score',
      cell: (t) => (
        <span className="font-mono font-bold text-cyan-800 text-sm">{t.priority_score.toFixed(1)}</span>
      ),
    },
    {
      header: 'Patient / MRN',
      cell: (t) => (
        <div>
          <p className="font-bold text-slate-900">{t.patient_name || t.patient_id}</p>
          <p className="text-[10px] text-slate-400 font-mono">{t.patient_mrn}</p>
        </div>
      ),
    },
    {
      header: 'Status',
      cell: (t) => <StatusBadge status={t.state} />,
    },
    {
      header: 'Attempts',
      cell: (t) => (
        <span className="font-mono text-slate-700">{t.attempt_count} / {t.max_attempts}</span>
      ),
    },
    {
      header: 'Next Action / Callback',
      cell: (t) => (
        <span className="font-mono text-slate-600 text-[11px]">
          {t.scheduled_callback_at ? (
            <span className="text-purple-700 font-bold">Callback: {new Date(t.scheduled_callback_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          ) : t.next_attempt_at ? (
            new Date(t.next_attempt_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          ) : (
            'Immediate'
          )}
        </span>
      ),
    },
    {
      header: 'Cutoff Risk',
      cell: (t) => (
        <span className="font-mono text-slate-500 text-[11px]">
          {t.clinical_cutoff_at ? new Date(t.clinical_cutoff_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
        </span>
      ),
    },
    {
      header: 'Action',
      cell: (t) => (
        <Button
          size="sm"
          variant="outline"
          onClick={async () => {
            await api.simulateCall(t.id, 'COMPLETED');
            setStepMessage(`Simulated call completed for ${t.patient_name}`);
            reloadData();
          }}
        >
          Trigger Call
        </Button>
      ),
    },
  ];

  const callbackTasks = tasks.filter(t => (t.state === 'CALLBACK_SCHEDULED' || t.scheduled_callback_at) && t.state !== 'COMPLETED' && t.state !== 'ESCALATED' && t.state !== 'CLOSED' && t.state !== 'FAILED');
  const retryTasks = tasks.filter(t => t.state === 'RETRY_SCHEDULED' || t.state === 'MANUAL_FOLLOW_UP');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Outreach Operations & Live Queue Control Room"
        subtitle={`Active Campaign: ${activeCampaignName}`}
        badge={<Badge variant="amber">CAMPAIGN MANAGER</Badge>}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              loading={loading}
              onClick={() => handleSimulateStep()}
              icon={<Play className="w-4 h-4" />}
            >
              Simulate Queue Step
            </Button>
            <Button
              variant="danger"
              loading={loading}
              onClick={handleSimulateUrgentCall}
              icon={<PhoneCall className="w-4 h-4" />}
            >
              Simulate Urgent Call
            </Button>
            <Button
              variant="secondary"
              onClick={reloadData}
              icon={<RefreshCw className="w-4 h-4" />}
            >
              Refresh
            </Button>
          </div>
        }
      />

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTab('QUEUE')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
            activeTab === 'QUEUE' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          QUEUE ({tasks.length})
        </button>
        <button
          onClick={() => setActiveTab('CAMPAIGNS')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
            activeTab === 'CAMPAIGNS' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          CAMPAIGNS ({campaigns.length})
        </button>
        <button
          onClick={() => setActiveTab('CALLBACKS')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
            activeTab === 'CALLBACKS' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          CALLBACKS ({callbackTasks.length})
        </button>
        <button
          onClick={() => setActiveTab('RETRIES')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
            activeTab === 'RETRIES' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          RETRIES ({retryTasks.length})
        </button>
        <button
          onClick={() => setActiveTab('ANALYTICS')}
          className={`pb-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
            activeTab === 'ANALYTICS' ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          ANALYTICS
        </button>
      </div>

      {stepMessage && (
        <div className="p-3 bg-cyan-50 border border-cyan-200 rounded-lg text-cyan-900 text-xs font-medium flex items-center justify-between">
          <span>{stepMessage}</span>
          <button onClick={() => setStepMessage(null)} className="text-cyan-700 font-bold hover:text-cyan-950">✕</button>
        </div>
      )}

      {/* 1. QUEUE TAB VIEW */}
      {activeTab === 'QUEUE' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="border-cyan-300 bg-cyan-50/20">
              <CardContent className="p-4">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase">Active Calls</span>
                  <Activity className="w-4 h-4 text-cyan-700" />
                </div>
                <div className="text-2xl font-bold text-slate-900 tracking-tight">
                  {summary?.active_capacity ?? 0} / {summary?.capacity_limit ?? 10}
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 mt-2 overflow-hidden">
                  <div
                    className="bg-cyan-700 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, ((summary?.active_capacity ?? 0) / (summary?.capacity_limit ?? 10)) * 100)}%` }}
                  ></div>
                </div>
                <span className="text-[10px] text-slate-500 mt-1 block font-mono">FOR UPDATE SKIP LOCKED</span>
              </CardContent>
            </Card>

            <MetricCard
              title="Queue Depth"
              value={summary?.queue_depth ?? tasks.length}
              subtext="Pending Outreach Tasks"
              icon={<Clock className="w-5 h-5 text-emerald-700" />}
              variant="sage"
            />
            <MetricCard
              title="Cutoff Risk"
              value={summary?.cutoff_risk_count ?? 0}
              subtext="Priority Surge Applied"
              icon={<AlertTriangle className="w-5 h-5 text-amber-700" />}
              variant="amber"
            />
            <MetricCard
              title="Escalated Tasks"
              value={summary?.state_breakdown?.ESCALATED ?? 0}
              subtext="In Clinical Inbox"
              icon={<ShieldAlert className="w-5 h-5 text-red-700" />}
              variant="coral"
            />
          </div>

          <Card>
            <CardHeader action={<Badge variant="slate">SELECT FOR UPDATE SKIP LOCKED</Badge>}>
              <CardTitle>Dynamic Prioritization Queue & Call State</CardTitle>
            </CardHeader>
            {tasks.length === 0 ? (
              <EmptyState
                title="No Outreach Tasks Currently Queued"
                description="No eligible outreach tasks are waiting in the queue. Create or start an outreach campaign to populate queue tasks."
                icon={<Clock className="w-10 h-10 text-slate-300" />}
              />
            ) : (
              <DataTable
                columns={queueColumns}
                data={tasks}
                keyExtractor={(t) => t.id}
              />
            )}
          </Card>
        </div>
      )}

      {/* 2. CAMPAIGNS TAB VIEW */}
      {activeTab === 'CAMPAIGNS' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-bold text-slate-900">Hospital Outreach Campaigns Register</h2>
              <p className="text-xs text-slate-500">Manage campaign lifecycle states (DRAFT/READY → RUNNING → PAUSED → COMPLETED)</p>
            </div>
            <Button
              variant="primary"
              icon={<Plus className="w-4 h-4" />}
              onClick={() => setIsCreateCampaignOpen(true)}
            >
              Create New Campaign
            </Button>
          </div>

          {campaigns.length === 0 ? (
            <Card>
              <EmptyState
                title="No Outreach Campaigns Created"
                description="No outreach campaigns have been created for this hospital network."
                icon={<Megaphone className="w-10 h-10 text-slate-300" />}
                action={
                  <Button variant="primary" size="sm" onClick={() => setIsCreateCampaignOpen(true)} icon={<Plus className="w-4 h-4" />}>
                    Create Campaign
                  </Button>
                }
              />
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {campaigns.map((c) => (
                <Card key={c.id} className="border-slate-200">
                  <CardHeader action={<StatusBadge status={c.status} />}>
                    <CardTitle>{c.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-xs text-slate-600">{c.description || 'Post-discharge outreach campaign for acute recovery monitoring.'}</p>
                    <div className="grid grid-cols-3 gap-2 text-xs font-mono bg-slate-50 p-2.5 rounded border border-slate-100">
                      <div>
                        <span className="text-[10px] text-slate-400 block font-semibold">PRIORITY</span>
                        <span className="font-bold text-cyan-800">{c.priority_score} / 10</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block font-semibold">CONCURRENCY</span>
                        <span className="font-bold text-slate-800">{c.max_concurrent_calls} max</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block font-semibold">WINDOW</span>
                        <span className="font-bold text-slate-800">{c.calling_start_hour}:00-{c.calling_end_hour}:00</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                      {(c.status === 'READY' || c.status === 'DRAFT' || c.status === 'PAUSED') && (
                        <Button
                          size="sm"
                          variant="sage"
                          icon={<Play className="w-3.5 h-3.5" />}
                          onClick={() => handleStatusChange(c.id, 'RUNNING')}
                        >
                          {c.status === 'PAUSED' ? 'Resume Campaign' : 'Start Campaign'}
                        </Button>
                      )}

                      {c.status === 'RUNNING' && (
                        <Button
                          size="sm"
                          variant="secondary"
                          icon={<Pause className="w-3.5 h-3.5" />}
                          onClick={() => handleStatusChange(c.id, 'PAUSED')}
                        >
                          Pause Campaign
                        </Button>
                      )}

                      {c.status !== 'COMPLETED' && (
                        <Button
                          size="sm"
                          variant="outline"
                          icon={<CheckCircle className="w-3.5 h-3.5" />}
                          onClick={() => handleStatusChange(c.id, 'COMPLETED')}
                        >
                          Complete Campaign
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 3. CALLBACKS TAB VIEW */}
      {activeTab === 'CALLBACKS' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-base font-bold text-slate-900">Patient Scheduled Callbacks</h2>
              <p className="text-xs text-slate-500">Tasks with explicitly requested patient callback times</p>
            </div>
            <Button
              variant="primary"
              icon={<Calendar className="w-4 h-4" />}
              onClick={() => setIsScheduleCallbackOpen(true)}
            >
              Schedule New Callback
            </Button>
          </div>

          <Card>
            <CardHeader action={<Badge variant="purple">{callbackTasks.length} Callback(s) Scheduled</Badge>}>
              <CardTitle>Explicit Callback Queue</CardTitle>
            </CardHeader>
            {callbackTasks.length === 0 ? (
              <EmptyState
                title="No Callbacks Scheduled"
                description="Patient-requested callbacks will appear here when scheduled during intake calls or by operational staff."
                icon={<Calendar className="w-10 h-10 text-slate-300" />}
                action={
                  <Button variant="primary" size="sm" onClick={() => setIsScheduleCallbackOpen(true)} icon={<Calendar className="w-4 h-4" />}>
                    Schedule Callback
                  </Button>
                }
              />
            ) : (
              <DataTable
                columns={[
                  {
                    header: 'Patient / MRN',
                    cell: (t) => (
                      <div>
                        <p className="font-bold text-slate-900">{t.patient_name || t.patient_id}</p>
                        <p className="text-[10px] text-slate-400 font-mono">{t.patient_mrn}</p>
                      </div>
                    ),
                  },
                  {
                    header: 'Requested Time',
                    cell: (t) => (
                      <span className="font-mono font-bold text-purple-700">
                        {t.scheduled_callback_at ? new Date(t.scheduled_callback_at).toLocaleString() : 'N/A'}
                      </span>
                    ),
                  },
                  {
                    header: 'Priority Score',
                    cell: (t) => <span className="font-mono font-bold text-cyan-800">{t.priority_score.toFixed(1)}</span>,
                  },
                  {
                    header: 'Attempts',
                    cell: (t) => <span className="font-mono">{t.attempt_count} / {t.max_attempts}</span>,
                  },
                  {
                    header: 'Status',
                    cell: (t) => <StatusBadge status={t.state} />,
                  },
                  {
                    header: 'Action',
                    cell: (t) => (
                      <Button
                        size="sm"
                        variant="outline"
                        loading={loading}
                        onClick={async () => {
                          setLoading(true);
                          setStepMessage(null);
                          try {
                            const res = await api.simulateCall(t.id, 'COMPLETED');
                            setStepMessage(`Triggered callback call for ${t.patient_name || 'Patient'} -> Triage: ${res.triage_classification} (State: ${res.escalation_created ? 'ESCALATED' : 'COMPLETED'})`);
                            await reloadData();
                          } catch (err: any) {
                            setStepMessage(`Trigger Callback Failed: ${err.message}`);
                          } finally {
                            setLoading(false);
                          }
                        }}
                      >
                        Trigger Call Now
                      </Button>
                    ),
                  },
                ]}
                data={callbackTasks}
                keyExtractor={(t) => t.id}
              />
            )}
          </Card>
        </div>
      )}

      {/* 4. RETRIES TAB VIEW */}
      {activeTab === 'RETRIES' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-900">Outreach Retry Queue & Backoff Schedule</h2>
            <p className="text-xs text-slate-500">Tasks requiring retry attempts due to NO_ANSWER, BUSY, VOICEMAIL, or DROPPED calls</p>
          </div>

          <Card>
            <CardHeader action={<Badge variant="amber">{retryTasks.length} Task(s) in Retry Pipeline</Badge>}>
              <CardTitle>Retry Pipeline (Exponential Backoff: 15m → 60m → 240m)</CardTitle>
            </CardHeader>
            {retryTasks.length === 0 ? (
              <EmptyState
                title="No Retry Tasks"
                description="No tasks are currently scheduled for retry attempts."
                icon={<RefreshCw className="w-10 h-10 text-slate-300" />}
              />
            ) : (
              <DataTable
                columns={[
                  {
                    header: 'Patient / MRN',
                    cell: (t) => (
                      <div>
                        <p className="font-bold text-slate-900">{t.patient_name || t.patient_id}</p>
                        <p className="text-[10px] text-slate-400 font-mono">{t.patient_mrn}</p>
                      </div>
                    ),
                  },
                  {
                    header: 'Original Outcome',
                    cell: (t) => (
                      <Badge variant="amber">{(t.partial_context as any)?.last_outcome || 'NO_ANSWER'}</Badge>
                    ),
                  },
                  {
                    header: 'Attempt',
                    cell: (t) => (
                      <span className="font-mono font-bold text-slate-800">{t.attempt_count} / {t.max_attempts}</span>
                    ),
                  },
                  {
                    header: 'Next Retry Time',
                    cell: (t) => (
                      <span className="font-mono text-slate-700">
                        {t.next_attempt_at ? new Date(t.next_attempt_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Immediate'}
                      </span>
                    ),
                  },
                  {
                    header: 'Status',
                    cell: (t) => <StatusBadge status={t.state} />,
                  },
                  {
                    header: 'Action',
                    cell: (t) => (
                      <Button
                        size="sm"
                        variant="outline"
                        loading={loading}
                        onClick={async () => {
                          setLoading(true);
                          setStepMessage(null);
                          try {
                            const res = await api.simulateCall(t.id, 'COMPLETED');
                            setStepMessage(`Triggered retry call for ${t.patient_name || 'Patient'} -> Triage: ${res.triage_classification} (State: ${res.escalation_created ? 'ESCALATED' : 'COMPLETED'})`);
                            await reloadData();
                          } catch (err: any) {
                            setStepMessage(`Trigger Retry Failed: ${err.message}`);
                          } finally {
                            setLoading(false);
                          }
                        }}
                      >
                        Trigger Retry Now
                      </Button>
                    ),
                  },
                ]}
                data={retryTasks}
                keyExtractor={(t) => t.id}
              />
            )}
          </Card>
        </div>
      )}

      {/* 5. ANALYTICS TAB VIEW */}
      {activeTab === 'ANALYTICS' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-base font-bold text-slate-900">Hospital Operations Analytics Dashboard</h2>
            <p className="text-xs text-slate-500">Real-time operational metrics derived dynamically from database records</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Outreach Contact Rate"
              value={analytics?.contact_rate !== undefined ? `${(analytics.contact_rate * 100).toFixed(0)}%` : '0%'}
              subtext="Completed Tasks / Eligible Tasks"
              icon={<BarChart2 className="w-5 h-5 text-emerald-700" />}
              variant="sage"
            />
            <MetricCard
              title="Total Ingested Patients"
              value={analytics?.total_patients ?? 0}
              subtext="Managed Patients in Hospital"
              icon={<Users className="w-5 h-5 text-cyan-700" />}
              variant="eucalyptus"
            />
            <MetricCard
              title="Total Calls Attempted"
              value={analytics?.total_calls_attempted ?? 0}
              subtext="Completed AI Outreach Calls"
              icon={<PhoneCall className="w-5 h-5 text-amber-700" />}
              variant="amber"
            />
            <MetricCard
              title="Average Attempts"
              value={analytics?.average_attempts_per_contact !== undefined ? `${analytics.average_attempts_per_contact} calls` : '0.0 calls'}
              subtext="Per Contacted Patient"
              icon={<ArrowUpRight className="w-5 h-5 text-purple-700" />}
              variant="lavender"
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Queue Task State Distribution Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(summary?.state_breakdown || {}).length === 0 ? (
                <EmptyState
                  title="Not Enough Operational Data"
                  description="Analytics and task breakdown will appear as outreach activity is recorded in the database."
                  icon={<BarChart2 className="w-10 h-10 text-slate-300" />}
                />
              ) : (
                <div className="space-y-3">
                  {Object.entries(summary?.state_breakdown || {}).map(([state, count]) => (
                    <div key={state} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-700">{state}</span>
                        <span className="font-mono text-slate-900">{count} tasks</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-cyan-700 h-2 rounded-full"
                          style={{ width: `${Math.min(100, (count / maxTaskCount(summary?.state_breakdown)) * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* CREATE CAMPAIGN MODAL */}
      <Modal
        isOpen={isCreateCampaignOpen}
        onClose={() => setIsCreateCampaignOpen(false)}
        title="Create New Outreach Campaign"
        subtitle="Configure hospital campaign parameters and eligibility rules"
      >
        <form onSubmit={handleCreateCampaign} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Campaign Name</label>
            <input
              type="text"
              required
              value={newCampaignName}
              onChange={e => setNewCampaignName(e.target.value)}
              placeholder="e.g. Post-Op Wound Care Follow-Up"
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Priority (1-10)</label>
              <input
                type="number"
                min={1}
                max={10}
                value={newCampaignPriority}
                onChange={e => setNewCampaignPriority(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Max Concurrency</label>
              <input
                type="number"
                min={1}
                max={20}
                value={newCampaignConcurrency}
                onChange={e => setNewCampaignConcurrency(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Window (Hours)</label>
              <input
                type="number"
                min={12}
                max={168}
                value={newCampaignFollowUpHours}
                onChange={e => setNewCampaignFollowUpHours(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsCreateCampaignOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Create Campaign
            </Button>
          </div>
        </form>
      </Modal>

      {/* SCHEDULE CALLBACK MODAL */}
      <Modal
        isOpen={isScheduleCallbackOpen}
        onClose={() => setIsScheduleCallbackOpen(false)}
        title="Schedule Patient Callback"
        subtitle="Set requested date/time for explicit callback attempt"
      >
        <form onSubmit={handleScheduleCallback} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select Patient Task</label>
            <select
              required
              value={selectedTaskForCallback}
              onChange={e => setSelectedTaskForCallback(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800"
            >
              <option value="">-- Choose Patient Task --</option>
              {tasks.map(t => (
                <option key={t.id} value={t.id}>
                  {t.patient_name || t.patient_id} ({t.patient_mrn}) - State: {t.state}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Requested Callback Date & Time</label>
            <input
              type="datetime-local"
              required
              value={callbackTimeInput}
              onChange={e => setCallbackTimeInput(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button variant="ghost" size="sm" type="button" onClick={() => setIsScheduleCallbackOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" type="submit">
              Schedule Callback
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

function maxTaskCount(breakdown?: Record<string, number>): number {
  if (!breakdown) return 1;
  const values = Object.values(breakdown);
  return Math.max(...values, 1);
}
