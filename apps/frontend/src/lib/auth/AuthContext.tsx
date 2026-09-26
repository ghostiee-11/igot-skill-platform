"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { User, UserRole } from "@/lib/types";
import { fetchApi } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  token: null,
  isLoading: true,
  login: () => {},
  logout: () => {},
  updateUser: () => {},
  isAdmin: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem("karmayogi_token");
      const savedUserStr = localStorage.getItem("karmayogi_user");

      if (savedToken && savedUserStr) {
        try {
          const parsedUser = JSON.parse(savedUserStr);
          setToken(savedToken);
          setUser(parsedUser);
          
          // Verify with backend me endpoint in background
          fetchApi<any>("/auth/me")
            .then((res) => {
              const refreshedUser: User = {
                id: res.user_id,
                email: res.email,
                full_name: res.full_name,
                role: res.role,
                onboarding_completed: res.onboarding_completed,
              };
              setUser(refreshedUser);
              localStorage.setItem("karmayogi_user", JSON.stringify(refreshedUser));
            })
            .catch((err: { status?: number }) => {
              // Only a rejected token signs out; network errors or a restarting backend keep the cached session.
              if (err?.status === 401 || err?.status === 403) {
                localStorage.removeItem("karmayogi_token");
                localStorage.removeItem("karmayogi_user");
                setUser(null);
                setToken(null);
              }
            });
        } catch (e) {
          localStorage.removeItem("karmayogi_token");
          localStorage.removeItem("karmayogi_user");
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem("karmayogi_token", newToken);
    localStorage.setItem("karmayogi_user", JSON.stringify(newUser));

    // Route based on onboarding status
    if (!newUser.onboarding_completed && newUser.role !== "admin") {
      router.push("/onboarding");
    } else {
      router.push("/home");
    }
  };

  const logout = () => {
    localStorage.removeItem("karmayogi_token");
    localStorage.removeItem("karmayogi_user");
    setUser(null);
    setToken(null);
    router.push("/");
  };

  const updateUser = (fields: Partial<User>) => {
    if (!user) return;
    const updated = { ...user, ...fields };
    setUser(updated);
    localStorage.setItem("karmayogi_user", JSON.stringify(updated));
  };

  const isAdmin = user?.role === "admin";

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        updateUser,
        isAdmin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
