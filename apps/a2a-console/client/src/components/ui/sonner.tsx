import { Toaster as Sonner, toast } from 'sonner';

export function Toaster() {
  return (
    <Sonner
      position="top-right"
      richColors
      closeButton
      duration={3000}
      toastOptions={{
        classNames: {
          toast: 'border border-border bg-background text-foreground shadow-md',
        },
      }}
    />
  );
}

export { toast };
