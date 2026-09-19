import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Building, Megaphone, Stethoscope, ArrowRight, Activity, CheckCircle2, Lock } from 'lucide-react';
import { api } from '../services/api';
import type { User } from '../types';

interface Props {
  onLoginSuccess: (user: User) => void;
}

export const LoginPage: React.FC<Props> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('admin@metrohealth.org');
  const [password, setPassword] = useState('MetroAdmin123!');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email, password);
      onLoginSuccess(res.user);
      
      switch (res.user.role) {
        case 'PLATFORM_ADMIN':
          navigate('/platform');
          break;
        case 'HOSPITAL_ADMIN':
          navigate('/hospital');
          break;
        case 'CAMPAIGN_MANAGER':
          navigate('/campaigns');
          break;
        case 'CLINICAL_REVIEWER':
          navigate('/review');
          break;
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoUser = (e: string, p: string) => {
    setEmail(e);
    setPassword(p);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-4xl bg-white border border-slate-200 shadow-xl rounded-2xl overflow-hidden grid grid-cols-1 md:grid-cols-12">
        {/* LEFT SIDE: Brand & Product Identity */}
        <div className="md:col-span-6 bg-slate-900 text-white p-8 md:p-10 flex flex-col justify-between relative overflow-hidden border-b md:border-b-0 md:border-r border-slate-800">
          {/* Subtle clinical grid accent background */}
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#0e7490_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none"></div>

          <div className="relative z-10">
            <div className="inline-flex items-center space-x-2.5 px-3 py-1 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300 text-xs font-semibold mb-6">
              <Activity className="w-3.5 h-3.5" />
              <span>CLINICAL COMMAND CENTER</span>
            </div>

            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-cyan-700 flex items-center justify-center text-white font-black text-xl tracking-wider shadow-md">
                PC
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white">POSTCARE</h1>
                <p className="text-xs font-semibold text-cyan-400 uppercase tracking-widest">Outreach Operations</p>
              </div>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed font-normal mt-4">
              Coordinate patient outreach, clinical triage, escalation and follow-up across hospital networks with multi-agent AI safety consensus.
            </p>

            <div className="mt-8 space-y-3">
              <div className="flex items-start space-x-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Multi-tenant isolation & enterprise RBAC role enforcement</span>
              </div>
              <div className="flex items-start space-x-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Atomic FOR UPDATE SKIP LOCKED queue concurrency engine</span>
              </div>
              <div className="flex items-start space-x-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>Dual-LLM consensus & strict protocol evidence auditing</span>
              </div>
            </div>
          </div>

          <div className="relative z-10 mt-10 pt-6 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
            <span>HIPAA-COMPLIANT PLATFORM</span>
            <span>v2.4.0 OPERATIONAL</span>
          </div>
        </div>

        {/* RIGHT SIDE: Professional Login Card */}
        <div className="md:col-span-6 p-8 md:p-10 bg-white flex flex-col justify-between">
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Sign In to Operations Console</h2>
              <p className="text-xs text-slate-500 mt-1">Enter your clinical credentials or select a demo persona below.</p>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center space-x-2">
                <Lock className="w-4 h-4 shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Work Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@hospital.org"
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-900 focus:bg-white focus:outline-none focus:border-cyan-700 focus:ring-1 focus:ring-cyan-700 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-900 focus:bg-white focus:outline-none focus:border-cyan-700 focus:ring-1 focus:ring-cyan-700 transition-all"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-cyan-800 hover:bg-cyan-900 text-white text-xs font-bold rounded-lg flex items-center justify-center space-x-2 shadow-xs transition-colors cursor-pointer"
              >
                <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>

          {/* Quick Demo Persona Login */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
              Quick Demo Persona Login
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setDemoUser('admin@platform.gov', 'AdminPass123!')}
                className="p-2.5 border border-slate-200 rounded-lg bg-slate-50/50 hover:bg-cyan-50/50 hover:border-cyan-300 text-left transition-colors flex items-start space-x-2.5 cursor-pointer"
              >
                <Shield className="w-4 h-4 text-purple-700 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-900 text-xs">Platform Admin</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">Multi-hospital operations</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setDemoUser('admin@metrohealth.org', 'MetroAdmin123!')}
                className="p-2.5 border border-slate-200 rounded-lg bg-slate-50/50 hover:bg-cyan-50/50 hover:border-cyan-300 text-left transition-colors flex items-start space-x-2.5 cursor-pointer"
              >
                <Building className="w-4 h-4 text-cyan-700 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-900 text-xs">Hospital Admin</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">Hospital config & patients</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setDemoUser('manager@metrohealth.org', 'Manager123!')}
                className="p-2.5 border border-slate-200 rounded-lg bg-slate-50/50 hover:bg-cyan-50/50 hover:border-cyan-300 text-left transition-colors flex items-start space-x-2.5 cursor-pointer"
              >
                <Megaphone className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-900 text-xs">Campaign Manager</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">Campaigns & outreach queue</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => setDemoUser('reviewer@metrohealth.org', 'Reviewer123!')}
                className="p-2.5 border border-slate-200 rounded-lg bg-slate-50/50 hover:bg-cyan-50/50 hover:border-cyan-300 text-left transition-colors flex items-start space-x-2.5 cursor-pointer"
              >
                <Stethoscope className="w-4 h-4 text-red-700 shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-900 text-xs">Clinical Reviewer</p>
                  <p className="text-[10px] text-slate-500 leading-tight mt-0.5">Clinical escalations & review</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
