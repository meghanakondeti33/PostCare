import React, { useState, useEffect } from 'react';
import { CheckCircle, Shield, MessageSquare, AlertTriangle, HelpCircle, Stethoscope, Clock, FileText, Check } from 'lucide-react';
import { api } from '../services/api';
import type { Escalation } from '../types';
import { Button } from '../components/ui/Button';
import { Badge, StatusBadge } from '../components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { EmptyState } from '../components/ui/States';

export const ClinicalReviewerPage: React.FC = () => {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [selectedEscalationId, setSelectedEscalationId] = useState<string | null>(null);
  const [detail, setDetail] = useState<any | null>(null);
  const [notes, setNotes] = useState('');
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'ALL' | 'URGENT' | 'OPEN' | 'RESOLVED'>('ALL');

  const loadEscalations = async () => {
    try {
      const res = await api.getEscalations();
      setEscalations(res);
      if (res.length > 0 && !selectedEscalationId) {
        setSelectedEscalationId(res[0].id);
      }
    } catch (err) {
      console.error('Error fetching escalations:', err);
    }
  };

  useEffect(() => {
    loadEscalations();
  }, []);

  const filteredEscalations = escalations.filter(e => {
    if (activeFilter === 'URGENT') return e.priority === 'URGENT' && e.state !== 'RESOLVED';
    if (activeFilter === 'OPEN') return e.state === 'ASSIGNED' || e.state === 'WAITING_FOR_INFORMATION' || e.state === 'OPEN' || e.state === 'IN_REVIEW';
    if (activeFilter === 'RESOLVED') return e.state === 'RESOLVED' || e.state === 'CLOSED';
    return true;
  });

  // Sync selected item when activeFilter changes
  useEffect(() => {
    if (filteredEscalations.length > 0) {
      const isStillInFilter = filteredEscalations.some(e => e.id === selectedEscalationId);
      if (!isStillInFilter) {
        setSelectedEscalationId(filteredEscalations[0].id);
      }
    } else {
      setSelectedEscalationId(null);
    }
  }, [activeFilter, escalations]);

  useEffect(() => {
    if (selectedEscalationId) {
      setLoadingDetail(true);
      api.getEscalationDetail(selectedEscalationId)
        .then(setDetail)
        .catch((err) => {
          console.error('Error fetching escalation detail:', err);
          setDetail(null);
        })
        .finally(() => setLoadingDetail(false));
    } else {
      setDetail(null);
    }
  }, [selectedEscalationId]);

  const handleResolve = async (state: string) => {
    if (!selectedEscalationId) return;
    try {
      await api.updateEscalation(selectedEscalationId, state, notes || 'Clinical review completed by attending RN.');
      setActionSuccess(`Escalation updated to state: ${state}`);
      setNotes('');
      await loadEscalations();
      const updatedDetail = await api.getEscalationDetail(selectedEscalationId);
      setDetail(updatedDetail);
      setTimeout(() => setActionSuccess(null), 3500);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center pb-3 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-red-700" />
            <span>Clinical Reviewer Escalation Workstation</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">3-Column Clinical Workflow: Triage Evidence, Dual-AI Consensus & Human Override</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="coral">{escalations.filter(e => e.priority === 'URGENT' && e.state !== 'RESOLVED').length} Urgent Case(s)</Badge>
          <Badge variant="slate">{escalations.length} Total Cases</Badge>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span className="font-semibold">{actionSuccess}</span>
        </div>
      )}

      {/* Empty State when zero escalations exist */}
      {escalations.length === 0 ? (
        <Card className="p-12">
          <EmptyState
            title="All Clear — No Escalations Require Review"
            description="No clinical escalations currently require review. Clinical alerts triggered by AI consensus or protocol rules will appear here."
            icon={<Check className="w-10 h-10 text-emerald-600" />}
          />
        </Card>
      ) : (
        /* 3-COLUMN CLINICAL WORKFLOW GRID */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
          
          {/* COLUMN 1: LEFT - PATIENT & ESCALATION LIST (3 cols) */}
          <div className="lg:col-span-3 space-y-3">
            <Card>
              <div className="p-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Inbox List</span>
                <span className="text-[10px] text-slate-500 font-mono">{filteredEscalations.length} items</span>
              </div>

              {/* Filter Tabs */}
              <div className="p-2 border-b border-slate-100 grid grid-cols-4 gap-1 text-[10px] font-bold">
                <button
                  onClick={() => setActiveFilter('ALL')}
                  className={`py-1 rounded text-center cursor-pointer ${activeFilter === 'ALL' ? 'bg-cyan-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
                >
                  ALL
                </button>
                <button
                  onClick={() => setActiveFilter('URGENT')}
                  className={`py-1 rounded text-center cursor-pointer ${activeFilter === 'URGENT' ? 'bg-red-700 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
                >
                  URGENT
                </button>
                <button
                  onClick={() => setActiveFilter('OPEN')}
                  className={`py-1 rounded text-center cursor-pointer ${activeFilter === 'OPEN' ? 'bg-amber-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
                >
                  OPEN
                </button>
                <button
                  onClick={() => setActiveFilter('RESOLVED')}
                  className={`py-1 rounded text-center cursor-pointer ${activeFilter === 'RESOLVED' ? 'bg-emerald-700 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
                >
                  RESOLVED
                </button>
              </div>

              {/* List Items */}
              <div className="p-2 space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto">
                {filteredEscalations.length === 0 ? (
                  <div className="p-4 text-center text-slate-400 text-xs">No escalations in filter</div>
                ) : (
                  filteredEscalations.map(esc => {
                    const isSelected = selectedEscalationId === esc.id;
                    return (
                      <div
                        key={esc.id}
                        onClick={() => setSelectedEscalationId(esc.id)}
                        className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-cyan-50/70 border-cyan-700 shadow-xs ring-1 ring-cyan-700'
                            : 'bg-white border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-bold text-slate-900 text-xs">{esc.patient_name || 'Patient Case'}</span>
                          <StatusBadge status={esc.priority} />
                        </div>
                        <p className="text-[11px] text-slate-600 line-clamp-2 leading-tight">{esc.trigger_reason}</p>
                        <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400 font-mono border-t border-slate-100 pt-1.5">
                          <span className="uppercase font-semibold">{esc.state}</span>
                          <span>{new Date(esc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </Card>
          </div>

          {/* COLUMN 2: CENTER - PATIENT SUMMARY, TRANSCRIPT, TIMELINE & OBSERVED SYMPTOMS (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            {loadingDetail && (
              <Card className="p-12 text-center text-slate-500 text-xs">
                Loading patient clinical summary & conversation transcript...
              </Card>
            )}

            {!loadingDetail && detail && (
              <>
                {/* Patient Summary Header */}
                <Card>
                  <CardHeader className="bg-slate-50/50">
                    <div>
                      <CardTitle>{detail.patient.first_name} {detail.patient.last_name}</CardTitle>
                      <p className="text-xs text-slate-500 font-mono mt-0.5">
                        MRN: {detail.patient.mrn} | DOB: {detail.patient.dob ?? 'N/A'} | Phone: {detail.patient.phone}
                      </p>
                    </div>
                    {detail.patient.high_risk_flag && <Badge variant="coral">HIGH RISK PATIENT</Badge>}
                  </CardHeader>
                  <CardContent className="space-y-3 pt-3">
                    <div className="p-2.5 bg-red-50 border border-red-200 rounded-md">
                      <span className="text-[11px] font-bold text-red-800 uppercase tracking-wider block mb-0.5">Primary Escalation Trigger</span>
                      <p className="text-xs text-red-900 font-semibold">{detail.escalation.trigger_reason}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 bg-slate-50 rounded border border-slate-100">
                        <span className="text-slate-400 text-[10px] block font-semibold">LANGUAGE PREFERENCE</span>
                        <span className="font-semibold text-slate-800">{detail.patient.preferred_language ?? 'English'}</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded border border-slate-100">
                        <span className="text-slate-400 text-[10px] block font-semibold">PRIMARY DIAGNOSIS</span>
                        <span className="font-semibold text-slate-800">{detail.patient.primary_diagnosis ?? 'Post-Acute Recovery'}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Observed Symptoms & Red Flags (Dynamic from Backend Record) */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-1.5 text-xs text-amber-900">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      <span>Observed Clinical Indicators</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex flex-wrap gap-1.5">
                      {detail.escalation.clinical_indicators && detail.escalation.clinical_indicators.length > 0 ? (
                        detail.escalation.clinical_indicators.map((ind: string, idx: number) => (
                          <Badge key={idx} variant="coral">{ind}</Badge>
                        ))
                      ) : (
                        <span className="text-xs text-slate-500 italic">No specific red flags flagged.</span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 mt-2 bg-slate-50 p-2 rounded border border-slate-100 italic">
                      "{detail.escalation.trigger_reason}"
                    </p>
                  </CardContent>
                </Card>

                {/* Conversation Transcript */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                      <MessageSquare className="w-4 h-4 text-cyan-700" />
                      <span>AI Outreach Conversation Transcript</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-slate-900 text-slate-100 p-3.5 rounded-md font-mono text-xs space-y-2 max-h-60 overflow-y-auto">
                      {detail.conversation?.transcript_json?.map((msg: any, i: number) => (
                        <div key={i} className="leading-relaxed">
                          <span className={msg.speaker?.toLowerCase().includes('patient') ? 'text-amber-400 font-bold' : 'text-cyan-400 font-bold'}>
                            [{msg.speaker}]:
                          </span>{' '}
                          <span className="text-slate-200">{msg.text}</span>
                        </div>
                      )) || (
                        <p className="text-slate-400 italic">No audio/text transcript logged for this session.</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            {!detail && !loadingDetail && (
              <Card className="p-12 text-center text-slate-500 text-xs">
                Select an escalation case from the left column inbox.
              </Card>
            )}
          </div>

          {/* COLUMN 3: RIGHT - TRIAGE, AI ASSESSMENTS, CONSENSUS, EVIDENCE & ACTIONS (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            {!loadingDetail && detail && (
              <>
                {/* Triage & Dual AI Assessments */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                      <Shield className="w-4 h-4 text-purple-700" />
                      <span>Dual-LLM AI Safety Consensus</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-md">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[11px] font-bold text-purple-900">
                          Model A Assessment — {detail.dual_assessment?.assessment_a?.agent_role || 'Protocol Focus'}
                        </span>
                        <Badge variant="purple">
                          {detail.dual_assessment?.assessment_a?.model 
                            ? (detail.dual_assessment.assessment_a.provider === 'gemini' 
                                ? (detail.dual_assessment.assessment_a.model === 'gemini-3.5-flash' ? 'Gemini 3.5 Flash' : `Gemini ${detail.dual_assessment.assessment_a.model}`)
                                : `${detail.dual_assessment.assessment_a.provider} ${detail.dual_assessment.assessment_a.model}`)
                            : 'Gemini 3.5 Flash'}
                        </Badge>
                      </div>
                      <p className="text-xs font-bold text-purple-950">
                        Classification: <span className="text-red-700">{detail.dual_assessment?.assessment_a?.classification ?? 'N/A'}</span>
                      </p>
                      <p className="text-[11px] text-purple-800 mt-1 italic">
                        {detail.dual_assessment?.assessment_a?.observations?.join(', ') || detail.dual_assessment?.assessment_a?.rationale || 'Protocol focus assessment complete.'}
                      </p>
                    </div>

                    <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-md">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-[11px] font-bold text-purple-900">
                          Model B Assessment — {detail.dual_assessment?.assessment_b?.agent_role || 'Holistic Focus'}
                        </span>
                        <Badge variant="purple">
                          {detail.dual_assessment?.assessment_b?.model 
                            ? (detail.dual_assessment.assessment_b.provider === 'gemini' 
                                ? (detail.dual_assessment.assessment_b.model === 'gemini-3.5-flash' ? 'Gemini 3.5 Flash' : `Gemini ${detail.dual_assessment.assessment_b.model}`)
                                : `${detail.dual_assessment.assessment_b.provider} ${detail.dual_assessment.assessment_b.model}`)
                            : 'Gemini 3.5 Flash'}
                        </Badge>
                      </div>
                      <p className="text-xs font-bold text-purple-950">
                        Classification: <span className="text-red-700">{detail.dual_assessment?.assessment_b?.classification ?? 'N/A'}</span>
                      </p>
                      <p className="text-[11px] text-purple-800 mt-1 italic">
                        {detail.dual_assessment?.assessment_b?.observations?.join(', ') || detail.dual_assessment?.assessment_b?.rationale || 'Holistic recovery assessment complete.'}
                      </p>
                    </div>

                    {/* Consensus Engine Audit */}
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1.5 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500 font-medium">Consensus Policy:</span>
                        <span className="font-mono font-bold text-slate-800">{detail.consensus_decision?.consensus_policy_used ?? 'STRICT_CONSERVATIVE'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500 font-medium">Model Disagreement:</span>
                        <span className="font-bold text-emerald-700">{detail.consensus_decision?.is_disagreement ? 'YES (Conservative Fallback Applied)' : 'NO (Unanimous)'}</span>
                      </div>
                      <p className="text-[11px] text-slate-700 pt-1 border-t border-slate-200 mt-1">
                        {detail.consensus_decision?.rationale ?? 'Consensus engine selected conservative highest-severity tier.'}
                      </p>
                    </div>
                  </CardContent>
                </Card>

                {/* Protocol Evidence */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-1.5 text-xs">
                      <FileText className="w-4 h-4 text-cyan-800" />
                      <span>Retrieved Protocol Evidence (RAG) & Safety Rules</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-xs">
                    {detail.escalation.evidence && detail.escalation.evidence.length > 0 ? (
                      <div className="space-y-1.5">
                        {detail.escalation.evidence.map((ev: string, idx: number) => (
                          <div key={idx} className="p-2 bg-slate-50 border border-slate-200 rounded font-mono text-[11px] text-slate-800 leading-relaxed">
                            {ev}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-400 italic">No RAG evidence records attached.</p>
                    )}
                  </CardContent>
                </Card>


                {/* CLINICAL REVIEWER ACTIONS & DECISION OVERRIDE */}
                <Card className="border-t-4 border-t-cyan-800">
                  <CardHeader>
                    <CardTitle className="text-xs uppercase tracking-wider text-slate-900 font-bold">
                      Clinical Reviewer Actions
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-700 mb-1">
                        Clinical Notes & Triage Resolution
                      </label>
                      <textarea
                        rows={3}
                        value={notes}
                        onChange={e => setNotes(e.target.value)}
                        placeholder="Document clinical action taken (e.g. Contacted patient, adjusted dosage, dispatched EMT, or marked false alert)..."
                        className="w-full p-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:border-cyan-800 focus:bg-white"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolve('IN_REVIEW')}
                        icon={<Clock className="w-3.5 h-3.5" />}
                      >
                        Acknowledge
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleResolve('WAITING_FOR_INFORMATION')}
                        icon={<HelpCircle className="w-3.5 h-3.5" />}
                      >
                        Request Info
                      </Button>
                      <Button
                        variant="sage"
                        size="sm"
                        className="col-span-2"
                        onClick={() => handleResolve('RESOLVED')}
                        icon={<CheckCircle className="w-3.5 h-3.5" />}
                      >
                        Resolve & Sync EHR
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>

        </div>
      )}
    </div>
  );
};
