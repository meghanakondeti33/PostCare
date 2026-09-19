import React, { useState, useEffect } from 'react';
import { X, Calendar, Activity, PhoneCall, AlertTriangle, Database, Clock } from 'lucide-react';
import { api } from '../services/api';
import type { PatientTimeline } from '../types';

interface Props {
  patientId: string | null;
  onClose: () => void;
}

export const PatientTimelineModal: React.FC<Props> = ({ patientId, onClose }) => {
  const [data, setData] = useState<PatientTimeline | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (patientId) {
      setLoading(true);
      setError(null);
      api.getPatientTimeline(patientId)
        .then(res => setData(res))
        .catch(err => setError(err.message || 'Failed to load timeline'))
        .finally(() => setLoading(false));
    } else {
      setData(null);
    }
  }, [patientId]);

  if (!patientId) return null;

  const renderEventIcon = (type: string) => {
    switch (type) {
      case 'DISCHARGE':
        return <Calendar className="w-4 h-4 text-emerald-600" />;
      case 'QUEUE_TASK':
        return <Clock className="w-4 h-4 text-cyan-600" />;
      case 'CALL_ATTEMPT':
        return <PhoneCall className="w-4 h-4 text-teal-600" />;
      case 'CLINICAL_ESCALATION':
        return <AlertTriangle className="w-4 h-4 text-rose-600" />;
      case 'EHR_SYNC':
        return <Database className="w-4 h-4 text-purple-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-600" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl overflow-y-auto flex flex-col border-l border-slate-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50 sticky top-0 z-10">
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-semibold text-slate-900">
                {data ? `${data.patient.first_name} ${data.patient.last_name}` : 'Patient Timeline'}
              </h2>
              {data?.patient.high_risk_flag && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded badge-coral">HIGH RISK</span>
              )}
            </div>
            {data && (
              <p className="text-xs text-slate-500 mt-1">
                MRN: <span className="font-mono">{data.patient.mrn}</span> | Language: {data.patient.preferred_language} | Phone: {data.patient.phone}
              </p>
            )}
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-200 rounded-full text-slate-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 flex-1">
          {loading && (
            <div className="flex justify-center items-center py-12 text-slate-500 text-sm">
              Loading chronological patient operational timeline...
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-md text-rose-700 text-sm">
              {error}
            </div>
          )}

          {data && (
            <div className="space-y-6">
              {/* Encounters Summary */}
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">Encounters & Diagnoses</h3>
                {data.encounters.map(enc => (
                  <div key={enc.id} className="text-sm text-slate-800">
                    <span className="font-semibold">{enc.primary_diagnosis}</span> ({enc.care_setting}) - Discharged: {new Date(enc.discharge_date).toLocaleDateString()}
                  </div>
                ))}
              </div>

              {/* Chronological Timeline */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-4">Chronological Audit Journey</h3>
                <div className="relative pl-6 border-l-2 border-slate-200 space-y-6">
                  {data.timeline.map((ev, idx) => (
                    <div key={idx} className="relative group">
                      {/* Event Dot */}
                      <div className="absolute -left-[31px] top-0 p-1.5 rounded-full bg-white border border-slate-200 shadow-xs">
                        {renderEventIcon(ev.event_type)}
                      </div>

                      <div className="bg-white border border-slate-200 rounded-lg p-4 hover:border-teal-300 transition-colors">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="text-sm font-semibold text-slate-900">{ev.title}</h4>
                          <span className="text-xs text-slate-400 font-mono">
                            {new Date(ev.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 mt-1">{ev.description}</p>
                        {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                          <div className="mt-2 text-xs bg-slate-50 p-2 rounded border border-slate-100 font-mono text-slate-700">
                            {JSON.stringify(ev.metadata, null, 2)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
