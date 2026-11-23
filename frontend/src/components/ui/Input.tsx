import { useId, type InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
}

export function Input({ label, id, ...props }: InputProps) {
  const fallbackId = useId()
  const inputId = id ?? fallbackId
  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={inputId}
        className="block w-full rounded-lg border-0 px-3 py-2 text-sm text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        {...props}
      />
    </div>
  )
}
