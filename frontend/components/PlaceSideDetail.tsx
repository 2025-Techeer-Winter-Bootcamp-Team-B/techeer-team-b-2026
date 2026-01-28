import React from 'react';
import { X, TrainFront, GraduationCap, MapPin, Building2 } from 'lucide-react';

interface PlaceInfo {
  id: string;
  name: string;
  address: string;
  category?: string;
  lineName?: string;
  lineColor?: string;
  type: 'station' | 'school' | 'place';
}

interface ApartmentSummary {
  id: string;
  aptId: number;
  name: string;
  priceLabel: string;
  location: string;
  lat: number;
  lng: number;
  isSpeculationArea?: boolean;
}

interface PlaceSideDetailProps {
  place: PlaceInfo;
  apartments: ApartmentSummary[];
  onClose: () => void;
  onApartmentClick?: (aptId: number) => void;
}

export const PlaceSideDetail: React.FC<PlaceSideDetailProps> = ({
  place,
  apartments,
  onClose,
  onApartmentClick
}) => {
  const isStation = place.type === 'station';
  const isSchool = place.type === 'school';

  return (
    <div className="h-full flex flex-col overflow-hidden relative">
      {/* 헤더 */}
      <div className="sticky top-0 z-[100] px-7 py-5 border-b border-slate-200/50 bg-white/80 backdrop-blur-md" style={{ paddingTop: '1.75rem' }}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
              isStation ? 'bg-emerald-100 text-emerald-600'
              : isSchool ? 'bg-amber-100 text-amber-600'
              : 'bg-slate-100 text-slate-500'
            }`}>
              {isStation ? (
                <TrainFront className="w-5 h-5" />
              ) : isSchool ? (
                <GraduationCap className="w-5 h-5" />
              ) : (
                <MapPin className="w-5 h-5" />
              )}
            </div>
            <div className="min-w-0">
              <h2 className="text-[20px] font-black text-slate-900 leading-tight truncate">
                {place.name}
              </h2>
              <p className="text-[12px] text-slate-500 mt-1 flex items-center gap-1 truncate">
                <MapPin className="w-3 h-3" />
                <span className="truncate">{place.address}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2.5 hover:bg-white/80 rounded-full transition-colors text-slate-400 hover:text-slate-600 flex-shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 역/호선 정보 뱃지 */}
        <div className="mt-3 flex flex-wrap gap-2">
          {isStation && place.lineName && (
            <span
              className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold text-white shadow-sm"
              style={{ backgroundColor: place.lineColor || '#0f172a' }}
            >
              {place.lineName}
            </span>
          )}
          {place.category && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600">
              {place.category}
            </span>
          )}
        </div>
      </div>

      {/* 컨텐츠: 주변 아파트 리스트 */}
      <div
        className="flex-1 overflow-y-auto custom-scrollbar relative"
        onClick={(e) => e.stopPropagation()}
        onMouseDown={(e) => e.stopPropagation()}
        style={{
          background: `
            radial-gradient(1200px circle at 50% 40%, rgba(248, 250, 252, 0.8) 0%, transparent 60%),
            radial-gradient(900px circle at 70% 10%, rgba(147, 197, 253, 0.15) 0%, transparent 55%), 
            radial-gradient(800px circle at 30% 80%, rgba(196, 181, 253, 0.12) 0%, transparent 50%),
            linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)
          `,
          pointerEvents: 'auto'
        }}
      >
        <div className="px-6 py-4">
          <h3 className="text-[14px] font-bold text-slate-500 mb-2">
            주변 아파트
          </h3>
          {apartments.length === 0 ? (
            <p className="text-[13px] text-slate-400 py-6">
              주변에 아파트 정보를 찾지 못했습니다.
            </p>
          ) : (
            <div className="space-y-2">
              {apartments.map((apt) => (
                <button
                  key={apt.id}
                  onClick={() => onApartmentClick && onApartmentClick(apt.aptId)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/70 hover:bg-white shadow-sm border border-slate-100 text-left transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-4 h-4 text-slate-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[14px] font-bold text-slate-900 truncate">
                      {apt.name}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">
                      {apt.location}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-0.5">
                    <span className="text-[13px] font-extrabold text-slate-900 tabular-nums">
                      {apt.priceLabel}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

