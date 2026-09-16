"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const CLOSE_DELAY_MS = 350;

export function useHoverDropdown() {
  const [open, setOpen] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancelClose = useCallback(() => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  }, []);

  const openNow = useCallback(() => {
    cancelClose();
    setOpen(true);
  }, [cancelClose]);

  const closeSoon = useCallback(() => {
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(false), CLOSE_DELAY_MS);
  }, [cancelClose]);

  const openFromPointer = useCallback(
    (event: { pointerType: string }) => {
      if (event.pointerType === "mouse") openNow();
    },
    [openNow],
  );

  const closeFromPointer = useCallback(
    (event: { pointerType: string }) => {
      if (event.pointerType === "mouse") closeSoon();
    },
    [closeSoon],
  );

  const onOpenChange = useCallback(
    (nextOpen: boolean) => {
      cancelClose();
      setOpen(nextOpen);
    },
    [cancelClose],
  );

  useEffect(() => cancelClose, [cancelClose]);

  return {
    open,
    onOpenChange,
    triggerProps: {
      onPointerEnter: openFromPointer,
      onPointerLeave: closeFromPointer,
    },
    contentProps: {
      onPointerEnter: openFromPointer,
      onPointerLeave: closeFromPointer,
    },
  };
}
