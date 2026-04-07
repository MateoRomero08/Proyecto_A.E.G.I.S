import { useEffect } from "react";
import { Download, X } from "lucide-react";

interface PdfPreviewModalProps {
  isOpen: boolean;
  title: string;
  fileName: string;
  blobUrl: string | null;
  onClose: () => void;
  onDownload: () => void;
}

export function PdfPreviewModal({
  isOpen,
  title,
  fileName,
  blobUrl,
  onClose,
  onDownload,
}: PdfPreviewModalProps) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !blobUrl) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-5">
      <button
        type="button"
        aria-label="Cerrar previsualización"
        onClick={onClose}
        className="absolute inset-0 bg-slate-900/70"
      />

      <div className="relative w-full max-w-6xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        <div className="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div className="min-w-0">
            <h2 className="text-base sm:text-lg font-bold text-slate-900 truncate">{title}</h2>
            <p className="text-xs text-slate-500 truncate">{fileName}</p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onDownload}
              className="inline-flex items-center gap-2 bg-yellow-400 text-black font-semibold px-3 py-2 rounded-lg hover:bg-yellow-500 transition-colors"
            >
              <Download className="w-4 h-4" />
              Descargar
            </button>
            <button
              onClick={onClose}
              className="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-100"
              aria-label="Cerrar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="h-[70vh] bg-slate-100">
          <object data={blobUrl} type="application/pdf" className="w-full h-full">
            <iframe title={title} src={blobUrl} className="w-full h-full" />
          </object>
        </div>
      </div>
    </div>
  );
}
