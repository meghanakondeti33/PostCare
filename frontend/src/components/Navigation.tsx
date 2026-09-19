import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Search, Building, Megaphone, Stethoscope, LogOut } from 'lucide-react';
import type { User } from '../types';
import { api } from '../services/api';
import { PatientTimelineModal } from './PatientTimelineModal';

interface Props {
  user: User | null;
  onLogout: () => void;
}

export const Navigation: React.FC<Props> = ({ user, onLogout }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      const res = await api.getPatients(searchQuery);
      setSearchResults(res);
      setShowResults(true);
    } catch (err) {
      console.error(err);
    }
  };

  const roleNavItems = () => {
    if (!user) return [];

    switch (user.role) {
      case 'PLATFORM_ADMIN':
        return [
          { label: 'Platform Workstation', path: '/platform', icon: Building },
        ];
      case 'HOSPITAL_ADMIN':
        return [
          { label: 'Hospital Workstation', path: '/hospital', icon: Building },
        ];
      case 'CAMPAIGN_MANAGER':
        return [
          { label: 'Campaigns & Queue', path: '/campaigns', icon: Megaphone },
        ];
      case 'CLINICAL_REVIEWER':
        return [
          { label: 'Clinical Review Inbox', path: '/review', icon: Stethoscope },
        ];
      default:
        return [];
    }
  };

  return (
    <>
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-15 flex items-center justify-between">
          {/* Brand Identity */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-cyan-800 flex items-center justify-center text-white font-black text-sm tracking-wider shadow-xs">
              PC
            </div>
            <div>
              <h1 className="text-xs font-black text-slate-900 leading-none tracking-tight">POSTCARE OPERATIONS</h1>
              <span className="text-[10px] text-cyan-800 font-bold tracking-wider uppercase">Clinical Outreach Console</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {roleNavItems().map(item => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `px-3 py-1.5 rounded-md text-xs font-bold flex items-center space-x-1.5 transition-colors ${
                      isActive
                        ? 'bg-cyan-50 text-cyan-900 border border-cyan-200'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`
                  }
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Search Bar & User Status Controls */}
          <div className="flex items-center space-x-3">
            {/* Reusable Patient Search */}
            <div className="relative">
              <form onSubmit={handleSearch} className="relative">
                <input
                  type="text"
                  placeholder="Search Patient / MRN..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md text-xs w-44 sm:w-56 focus:w-64 focus:bg-white focus:outline-none focus:border-cyan-800 transition-all text-slate-900"
                />
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
              </form>

              {/* Quick Search Dropdown */}
              {showResults && searchResults.length > 0 && (
                <div className="absolute right-0 mt-1 w-64 bg-white border border-slate-200 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto">
                  {searchResults.map(p => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setSelectedPatientId(p.id);
                        setShowResults(false);
                      }}
                      className="w-full text-left px-3 py-2 hover:bg-cyan-50/50 border-b border-slate-100 text-xs flex justify-between cursor-pointer"
                    >
                      <span className="font-bold text-slate-900">{p.first_name} {p.last_name}</span>
                      <span className="text-slate-500 font-mono text-[11px]">{p.mrn}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Health Status Pill */}
            <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 bg-emerald-50 border border-emerald-200 rounded-full text-[10px] font-bold text-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse"></span>
              <span>SYSTEM HEALTHY</span>
            </div>

            {/* User Profile / Logout */}
            {user && (
              <div className="flex items-center space-x-2 border-l border-slate-200 pl-3">
                <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-slate-900 leading-tight">{user.full_name}</p>
                  <p className="text-[10px] text-cyan-800 font-mono font-bold uppercase">{user.role}</p>
                </div>
                <button
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-1.5 text-slate-500 hover:bg-slate-100 hover:text-red-700 rounded-md transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Patient Timeline Drawer Modal */}
      <PatientTimelineModal
        patientId={selectedPatientId}
        onClose={() => setSelectedPatientId(null)}
      />
    </>
  );
};
