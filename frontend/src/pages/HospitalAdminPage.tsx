import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, Users, Activity, Database, Search, Plus, X, ShieldCheck, Clock, Sliders, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import type { Patient, Hospital, Protocol, EHRRecord, PatientTimeline } from '../types';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { MetricCard } from '../components/ui/MetricCard';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DataTable, type Column } from '../components/ui/DataTable';
import { EmptyState } from '../components/ui/States';

export const HospitalAdminPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  const [ehrRecords, setEhrRecords] = useState<EHRRecord[]>([]);
  
  const [ingestSuccess, setIngestSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'PATIENTS' | 'DISCHARGES' | 'PROTOCOLS' | 'SETTINGS'>('OVERVIEW');
  
  // Patient search & filter state
  const [patientSearch, setPatientSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'HIGH_RISK' | 'NORMAL'>('ALL');
  const [selectedPatientTimeline, setSelectedPatientTimeline] = useState<PatientTimeline | null>(null);

  // New Protocol modal state
  const [showProtocolModal, setShowProtocolModal] = useState(false);
  const [protoName, setProtoName] = useState('');
  const [protoCategory, setProtoCategory] = useState('General');
  const [protoConditions, setProtoConditions] = useState('');
  const [protoRedFlags, setProtoRedFlags] = useState('');
  const [protoLoading, setProtoLoading] = useState(false);
  const [protoError, setProtoError] = useState<string | null>(null);

  const loadAllData = async () => {
    try {
      const [pats, hosps, stats, protos, ehrs] = await Promise.all([
        api.getPatients(),
        api.getHospitals(),
        api.getHospitalAnalytics().catch(() => null),
        api.getProtocols().catch(() => []),
        api.getEHRRecords().catch(() => []),
      ]);
      setPatients(pats);
      setHospitals(hosps);
      setAnalytics(stats);
      setProtocols(protos);
      setEhrRecords(ehrs);
    } catch (err) {
      console.error('Error loading Hospital Admin data:', err);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleSimulateIngest = async () => {
    setIngestSuccess(true);
    await loadAllData();
    setTimeout(() => setIngestSuccess(false), 4500);
  };

  const handleCreateProtocol = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!protoName.trim()) return;
    setProtoLoading(true);
    setProtoError(null);
    try {
      await api.createProtocol({
        name: protoName.trim(),
        category: protoCategory.trim() || 'General',
        target_conditions: protoConditions.split(',').map(s => s.trim()).filter(Boolean),
        red_flags: protoRedFlags.split(',').map(s => s.trim()).filter(Boolean),
        follow_up_questions: ["Have you experienced any worsening symptoms?"],
        escalation_contacts: ["Triage Nurse Desk"],
      });
      setShowProtocolModal(false);
      setProtoName('');
      setProtoConditions('');
      setProtoRedFlags('');
      const updatedProtos = await api.getProtocols();
      setProtocols(updatedProtos);
    } catch (err: any) {
      setProtoError(err.message || 'Failed to create protocol');
    } finally {
      setProtoLoading(false);
    }
  };

  const handleViewPatientTimeline = async (patientId: string) => {
    try {
      const timelineData = await api.getPatientTimeline(patientId);
      setSelectedPatientTimeline(timelineData);
    } catch (err) {
      console.error('Failed to load patient timeline:', err);
    }
  };

  const currentHospital = hospitals[0];

  // Filtered patients list
  const filteredPatients = patients.filter(p => {
    const matchesSearch = !patientSearch || 
      `${p.first_name} ${p.last_name}`.toLowerCase().includes(patientSearch.toLowerCase()) ||
      p.mrn.toLowerCase().includes(patientSearch.toLowerCase());
    const matchesRisk = 
      riskFilter === 'ALL' ||
      (riskFilter === 'HIGH_RISK' && p.high_risk_flag) ||
      (riskFilter === 'NORMAL' && !p.high_risk_flag);
    return matchesSearch && matchesRisk;
  });

  // Table columns for Patients
  const patientColumns: Column<Patient>[] = [
    {
      header: 'MRN',
      accessor: 'mrn',
      cell: (p) => <span className="font-mono font-bold text-slate-900">{p.mrn}</span>,
    },
    {
      header: 'Patient Name',
      cell: (p) => (
        <div>
          <p className="font-bold text-slate-900">{p.first_name} {p.last_name}</p>
          <p className="text-[10px] text-slate-400 font-mono">DOB: {p.dob ?? 'N/A'}</p>
        </div>
      ),
    },
    {
      header: 'Language / Phone',
      cell: (p) => (
        <div>
          <p className="text-slate-700">{p.preferred_language ?? 'English'}</p>
          <p className="text-[10px] text-slate-500 font-mono">{p.phone}</p>
        </div>
      ),
    },
    {
      header: 'Risk Flag',
      cell: (p) => (
        p.high_risk_flag ? (
          <Badge variant="coral">HIGH RISK</Badge>
        ) : (
          <Badge variant="sage">NORMAL</Badge>
        )
      ),
    },
    {
      header: 'Ingested Date',
      cell: (p) => <span className="font-mono text-slate-500">{new Date(p.created_at).toLocaleDateString()}</span>,
    },
    {
      header: 'Actions',
      cell: (p) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleViewPatientTimeline(p.id)}
          icon={<Clock className="w-3 h-3" />}
        >
          Timeline
        </Button>
      ),
    },
  ];

  // Table columns for Protocols
  const protocolColumns: Column<Protocol>[] = [
    {
      header: 'Protocol Name',
      cell: (pr) => (
        <div>
          <p className="font-bold text-slate-900">{pr.name}</p>
          <p className="text-[10px] text-slate-400 font-mono">v{pr.version} • ID: {pr.id.slice(0, 12)}</p>
        </div>
      ),
    },
    {
      header: 'Category',
      cell: (pr) => <Badge variant="lavender">{pr.category}</Badge>,
    },
    {
      header: 'Target Conditions',
      cell: (pr) => (
        <div className="flex flex-wrap gap-1">
          {pr.target_conditions && pr.target_conditions.length > 0 ? (
            pr.target_conditions.map((tc, idx) => (
              <span key={idx} className="px-1.5 py-0.5 bg-slate-100 text-slate-700 rounded text-[10px] font-medium">
                {tc}
              </span>
            ))
          ) : (
            <span className="text-slate-400 italic text-[10px]">General Post-Op</span>
          )}
        </div>
      ),
    },
    {
      header: 'Red Flags',
      cell: (pr) => (
        <div className="flex flex-wrap gap-1">
          {pr.red_flags && pr.red_flags.length > 0 ? (
            pr.red_flags.map((rf, idx) => (
              <span key={idx} className="px-1.5 py-0.5 bg-amber-50 text-amber-800 border border-amber-200 rounded text-[10px] font-semibold">
                {rf}
              </span>
            ))
          ) : (
            <span className="text-slate-400 italic text-[10px]">None specified</span>
          )}
        </div>
      ),
    },
    {
      header: 'RAG Index Status',
      cell: (pr) => (
        <Badge variant={pr.is_active ? 'eucalyptus' : 'slate'}>
          {pr.is_active ? 'INDEXED IN RAG' : 'INACTIVE'}
        </Badge>
      ),
    },
  ];

  // Table columns for EHR Discharge Records
  const ehrColumns: Column<EHRRecord>[] = [
    {
      header: 'Resource ID',
      cell: (e) => <span className="font-mono font-bold text-slate-900">{e.resource_id}</span>,
    },
    {
      header: 'Resource Type',
      cell: (e) => (
        <Badge variant={e.resource_type === 'Communication' ? 'purple' : e.resource_type === 'EscalationResolution' ? 'coral' : 'sage'}>
          {e.resource_type}
        </Badge>
      ),
    },
    {
      header: 'Patient ID',
      cell: (e) => <span className="font-mono text-slate-600 text-[11px]">{e.patient_id.slice(0, 16)}</span>,
    },
    {
      header: 'Synced At',
      cell: (e) => <span className="font-mono text-slate-500 text-[11px]">{new Date(e.synced_at).toLocaleString()}</span>,
    },
    {
      header: 'Payload Summary',
      cell: (e) => (
        <p className="text-[11px] text-slate-600 truncate max-w-xs font-mono">
          {JSON.stringify(e.data)}
        </p>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Hospital Operations Workstation"
        subtitle={currentHospital ? `Tenant Scoped: ${currentHospital.name} (${currentHospital.code})` : 'Hospital Operations Console'}
        badge={<Badge variant="eucalyptus">HOSPITAL ADMIN</Badge>}
        actions={
          <Button
            variant="primary"
            onClick={handleSimulateIngest}
            icon={<Upload className="w-4 h-4" />}
          >
            Ingest Discharge Feed
          </Button>
        }
      />

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-200 space-x-6 text-xs font-semibold overflow-x-auto">
        {(['OVERVIEW', 'PATIENTS', 'DISCHARGES', 'PROTOCOLS', 'SETTINGS'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
              activeTab === tab ? 'border-cyan-800 text-cyan-900 font-bold' : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {ingestSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3.5 rounded-lg text-xs flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="font-medium">Discharge Feed Ingested Successfully! New post-acute records checked for campaign eligibility.</span>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 1: OVERVIEW                                                           */}
      {/* ========================================================================= */}
      {activeTab === 'OVERVIEW' && (
        <div className="space-y-6">
          {/* Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Hospital Patients"
              value={analytics?.total_patients ?? patients.length}
              subtext="Active Ingested Feed"
              icon={<Users className="w-5 h-5 text-cyan-700" />}
              variant="eucalyptus"
            />
            <MetricCard
              title="Capacity Limit"
              value={currentHospital ? `${currentHospital.max_concurrent_calls} Calls` : '10 Calls'}
              subtext="Central Concurrency Lock"
              icon={<Activity className="w-5 h-5 text-emerald-700" />}
              variant="sage"
            />
            <MetricCard
              title="Contact Rate"
              value={analytics?.contact_rate !== undefined ? `${(analytics.contact_rate * 100).toFixed(0)}%` : '0%'}
              subtext="Outreach Efficiency"
              icon={<CheckCircle className="w-5 h-5 text-amber-700" />}
              variant="amber"
            />
            <MetricCard
              title="EHR Integration"
              value="FHIR R4"
              subtext="Mock EHR Auto-Sync"
              icon={<Database className="w-5 h-5 text-purple-700" />}
              variant="lavender"
            />
          </div>

          {/* Operational Workstation Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-xs uppercase tracking-wider text-slate-800 font-bold flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-800" />
                  <span>Facility Operational Status & Queue Breakdown</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <p className="text-[10px] text-slate-500 font-semibold uppercase">Total Tasks</p>
                    <p className="text-lg font-bold text-slate-900">{analytics?.total_outreach_tasks ?? 0}</p>
                  </div>
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md">
                    <p className="text-[10px] text-emerald-800 font-semibold uppercase">Completed</p>
                    <p className="text-lg font-bold text-emerald-950">{analytics?.total_completed_tasks ?? 0}</p>
                  </div>
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                    <p className="text-[10px] text-amber-800 font-semibold uppercase">Retries / Callbacks</p>
                    <p className="text-lg font-bold text-amber-950">{(analytics?.total_retry_tasks ?? 0) + (analytics?.total_callback_tasks ?? 0)}</p>
                  </div>
                  <div className="p-3 bg-rose-50 border border-rose-200 rounded-md">
                    <p className="text-[10px] text-rose-800 font-semibold uppercase">Escalations</p>
                    <p className="text-lg font-bold text-rose-950">{analytics?.total_escalations ?? 0}</p>
                  </div>
                </div>

                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-md flex justify-between items-center">
                  <div>
                    <p className="font-bold text-slate-900">{currentHospital?.name || 'Hospital Network'}</p>
                    <p className="text-[11px] text-slate-500">
                      Facility Code: <span className="font-mono">{currentHospital?.code || 'HOSP'}</span> • Timezone: {currentHospital?.timezone || 'UTC'}
                    </p>
                  </div>
                  <Badge variant="eucalyptus">OPERATIONAL</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xs uppercase tracking-wider text-slate-800 font-bold flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-purple-800" />
                  <span>Clinical Safety & Safeguards</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-md space-y-1">
                  <p className="font-bold text-purple-900">Consensus Policy</p>
                  <p className="text-[11px] text-purple-800">STRICT_CONSERVATIVE active across all outreach evaluations.</p>
                </div>
                <div className="p-2.5 bg-cyan-50 border border-cyan-200 rounded-md space-y-1">
                  <p className="font-bold text-cyan-950">RAG Knowledge Engine</p>
                  <p className="text-[11px] text-cyan-900">{protocols.length} active protocol documents indexed into tenant store.</p>
                </div>
                <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-md space-y-1">
                  <p className="font-bold text-emerald-950">Mock EHR Sync</p>
                  <p className="text-[11px] text-emerald-900">{ehrRecords.length} FHIR R4 communication resources synced.</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Ingested Patients Summary Table */}
          <Card>
            <CardHeader 
              action={
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setActiveTab('PATIENTS')}
                  icon={<ArrowRight className="w-3.5 h-3.5" />}
                >
                  View All Patients Directory
                </Button>
              }
            >
              <CardTitle>Recent Patient Discharge Records</CardTitle>
            </CardHeader>
            {patients.length === 0 ? (
              <EmptyState
                title="No Patients Ingested Yet"
                description="No patient discharge records have been imported for this hospital network. Click 'Ingest Discharge Feed' to load patient records."
                action={
                  <Button variant="primary" size="sm" onClick={handleSimulateIngest} icon={<Upload className="w-4 h-4" />}>
                    Ingest Discharge Feed
                  </Button>
                }
              />
            ) : (
              <DataTable
                columns={patientColumns}
                data={patients.slice(0, 5)}
                keyExtractor={(p) => p.id}
              />
            )}
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: PATIENTS                                                           */}
      {/* ========================================================================= */}
      {activeTab === 'PATIENTS' && (
        <div className="space-y-4">
          <Card>
            <CardHeader className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
              <CardTitle>Tenant-Scoped Patient Directory</CardTitle>
              <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-64">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search by name or MRN..."
                    value={patientSearch}
                    onChange={(e) => setPatientSearch(e.target.value)}
                    className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800 focus:bg-white"
                  />
                </div>
                <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-md text-xs font-semibold">
                  {(['ALL', 'HIGH_RISK', 'NORMAL'] as const).map(rf => (
                    <button
                      key={rf}
                      onClick={() => setRiskFilter(rf)}
                      className={`px-2 py-1 rounded text-[11px] transition-colors cursor-pointer ${
                        riskFilter === rf ? 'bg-white text-slate-900 shadow-sm font-bold' : 'text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      {rf === 'ALL' ? 'All' : rf === 'HIGH_RISK' ? 'High Risk' : 'Normal'}
                    </button>
                  ))}
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {filteredPatients.length === 0 ? (
                <div className="p-8">
                  <EmptyState
                    title="No Matching Patients"
                    description={patientSearch ? `No patient records match query "${patientSearch}".` : "No patients found for this hospital filter."}
                  />
                </div>
              ) : (
                <DataTable
                  columns={patientColumns}
                  data={filteredPatients}
                  keyExtractor={(p) => p.id}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: DISCHARGES                                                         */}
      {/* ========================================================================= */}
      {activeTab === 'DISCHARGES' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <MetricCard
              title="Discharged Records"
              value={patients.length}
              subtext="Total Post-Acute Feed"
              icon={<Users className="w-5 h-5 text-cyan-700" />}
              variant="eucalyptus"
            />
            <MetricCard
              title="Synced EHR Resources"
              value={ehrRecords.length}
              subtext="Communication & Task Resources"
              icon={<Database className="w-5 h-5 text-purple-700" />}
              variant="lavender"
            />
            <MetricCard
              title="Integration Engine"
              value="FHIR R4"
              subtext="Mock EHR Gateway"
              icon={<CheckCircle className="w-5 h-5 text-emerald-700" />}
              variant="sage"
            />
          </div>

          <Card>
            <CardHeader action={<Badge variant="purple">{ehrRecords.length} FHIR Resources</Badge>}>
              <CardTitle>Discharge Feed & Mock EHR Sync Logs</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {ehrRecords.length === 0 ? (
                <div className="p-8">
                  <EmptyState
                    title="No EHR Records Synced Yet"
                    description="As outreach calls complete and clinical reviewer resolutions are logged, FHIR R4 records will appear here."
                  />
                </div>
              ) : (
                <DataTable
                  columns={ehrColumns}
                  data={ehrRecords}
                  keyExtractor={(e) => e.id}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: PROTOCOLS                                                          */}
      {/* ========================================================================= */}
      {activeTab === 'PROTOCOLS' && (
        <div className="space-y-6">
          <Card>
            <CardHeader
              action={
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setShowProtocolModal(true)}
                  icon={<Plus className="w-4 h-4" />}
                >
                  Add Clinical Protocol
                </Button>
              }
            >
              <CardTitle>Hospital Clinical Protocols & RAG Knowledge Store</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {protocols.length === 0 ? (
                <div className="p-8">
                  <EmptyState
                    title="No Protocols Configured"
                    description="No hospital protocols found for this facility. Click 'Add Clinical Protocol' to create a protocol record."
                    action={
                      <Button variant="primary" size="sm" onClick={() => setShowProtocolModal(true)} icon={<Plus className="w-4 h-4" />}>
                        Add Clinical Protocol
                      </Button>
                    }
                  />
                </div>
              ) : (
                <DataTable
                  columns={protocolColumns}
                  data={protocols}
                  keyExtractor={(pr) => pr.id}
                />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: SETTINGS                                                           */}
      {/* ========================================================================= */}
      {activeTab === 'SETTINGS' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-wider text-slate-800 font-bold flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-800" />
                <span>Facility Configuration & Operating Hours</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Hospital Name</p>
                  <p className="font-bold text-slate-900 mt-0.5">{currentHospital?.name || 'St. Jude Healthcare'}</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Facility Code</p>
                  <p className="font-bold font-mono text-slate-900 mt-0.5">{currentHospital?.code || 'STJUDE'}</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Timezone</p>
                  <p className="font-bold text-slate-900 mt-0.5">{currentHospital?.timezone || 'America/New_York'}</p>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                  <p className="text-[10px] text-slate-500 uppercase font-semibold">Calling Window</p>
                  <p className="font-bold text-slate-900 mt-0.5">
                    {currentHospital?.calling_start_hour ?? 8}:00 AM - {currentHospital?.calling_end_hour ?? 20}:00 PM
                  </p>
                </div>
              </div>

              <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-md flex justify-between items-center">
                <div>
                  <p className="font-bold text-emerald-950">Concurrency Capacity Limit</p>
                  <p className="text-[11px] text-emerald-800">Max Concurrent Calls: {currentHospital?.max_concurrent_calls ?? 10} channels</p>
                </div>
                <Badge variant="eucalyptus">TENANT LOCKED</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-wider text-slate-800 font-bold flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-purple-800" />
                <span>Clinical Consensus Policy & EHR Integration</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              <div className="p-3.5 bg-purple-50 border border-purple-200 rounded-md space-y-1">
                <div className="flex justify-between items-center">
                  <p className="font-bold text-purple-950">Consensus Policy</p>
                  <Badge variant="purple">STRICT_CONSERVATIVE</Badge>
                </div>
                <p className="text-[11px] text-purple-800">
                  Enforces highest-severity fallback whenever AI triage assessment models disagree or red flags trigger.
                </p>
              </div>

              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                <div className="flex justify-between items-center">
                  <p className="font-bold text-slate-900">Mock EHR Gateway (FHIR R4)</p>
                  <Badge variant="sage">ACTIVE AUTO-SYNC</Badge>
                </div>
                <p className="text-[11px] text-slate-600 font-mono">
                  Endpoint: http://localhost:8000/api/v1/ehr/records
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* PATIENT TIMELINE DRAWER / MODAL                                           */}
      {/* ========================================================================= */}
      {selectedPatientTimeline && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-lg bg-white h-full shadow-2xl p-6 overflow-y-auto space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <div>
                <h3 className="font-bold text-base text-slate-900">
                  {selectedPatientTimeline.patient.first_name} {selectedPatientTimeline.patient.last_name}
                </h3>
                <p className="text-xs text-slate-500 font-mono">
                  MRN: {selectedPatientTimeline.patient.mrn} • DOB: {selectedPatientTimeline.patient.dob || 'N/A'}
                </p>
              </div>
              <button 
                onClick={() => setSelectedPatientTimeline(null)}
                className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Chronological Event Timeline</h4>
              {selectedPatientTimeline.timeline.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No events recorded for this patient yet.</p>
              ) : (
                <div className="space-y-2 border-l-2 border-slate-200 pl-4">
                  {selectedPatientTimeline.timeline.map((ev, idx) => (
                    <div key={idx} className="relative pb-2">
                      <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-cyan-800" />
                      <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-md">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-xs text-slate-900">{ev.title}</span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {new Date(ev.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{ev.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* NEW PROTOCOL MODAL                                                        */}
      {/* ========================================================================= */}
      {showProtocolModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-200 pb-3">
              <h3 className="font-bold text-base text-slate-900">Add Clinical Protocol</h3>
              <button onClick={() => setShowProtocolModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {protoError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-md">
                {protoError}
              </div>
            )}

            <form onSubmit={handleCreateProtocol} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Protocol Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Post-Op Cardiac Care Standard"
                  value={protoName}
                  onChange={(e) => setProtoName(e.target.value)}
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:border-cyan-800"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Category</label>
                <input
                  type="text"
                  placeholder="e.g. Cardiology, General, Orthopedics"
                  value={protoCategory}
                  onChange={(e) => setProtoCategory(e.target.value)}
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:border-cyan-800"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Conditions (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. Heart Failure, Post-CABG, Angina"
                  value={protoConditions}
                  onChange={(e) => setProtoConditions(e.target.value)}
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:border-cyan-800"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Red Flag Trigger Terms (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g. chest pain, shortness of breath, high fever"
                  value={protoRedFlags}
                  onChange={(e) => setProtoRedFlags(e.target.value)}
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:border-cyan-800"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200">
                <Button variant="outline" size="sm" type="button" onClick={() => setShowProtocolModal(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit" disabled={protoLoading}>
                  {protoLoading ? 'Saving...' : 'Save & Index Protocol'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
