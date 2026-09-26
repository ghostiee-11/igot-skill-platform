"use client";

import React, { useState } from "react";
import { Award, Lock, Mail, User as UserIcon, AlertCircle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchApi } from "@/lib/api";

export default function RegisterPage() {
  const { login } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);

    try {
      const data = await fetchApi<{
        access_token: string;
        user_id: number;
        email: string;
        full_name: string;
        role: "learner" | "admin";
        onboarding_completed: boolean;
      }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          role: "learner",
        }),
      });

      // Log in and automatically route to Onboarding wizard
      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
        onboarding_completed: false,
      });
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please verify details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-[#F8FAFC]">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="inline-flex h-12 w-12 rounded-xl bg-[#1E3A8A] text-white border border-blue-900 items-center justify-center mb-3 shadow-xs">
            <Award className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-bold text-[#0F172A] tracking-tight">Create Official Account</h2>
          <p className="text-xs text-slate-600 mt-1">
            Register your profile for statistical capacity building &amp; certifications
          </p>
        </div>

        <Card className="border-slate-200 shadow-sm bg-white rounded-2xl">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-bold text-[#0F172A]">Civil Servant Registration</CardTitle>
            <CardDescription className="text-xs text-slate-500">
              Step 1 of 2: Create login credentials before role onboarding
            </CardDescription>
          </CardHeader>

          <CardContent>
            {error && (
              <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Full Name (As in Official Records)
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Smt. Priya Sharma"
                    className="pl-9 text-xs border-slate-200 focus-visible:ring-[#1E3A8A] focus-visible:border-[#1E3A8A]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Government / Official Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="priya.sharma@mospi.gov.in"
                    className="pl-9 text-xs border-slate-200 focus-visible:ring-[#1E3A8A] focus-visible:border-[#1E3A8A]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Create Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 8 characters"
                    className="pl-9 text-xs border-slate-200 focus-visible:ring-[#1E3A8A] focus-visible:border-[#1E3A8A]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#0F172A] mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <Input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    className="pl-9 text-xs border-slate-200 focus-visible:ring-[#1E3A8A] focus-visible:border-[#1E3A8A]"
                  />
                </div>
              </div>

              <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl text-[11px] text-slate-700 leading-relaxed">
                <p className="font-semibold text-[#1E3A8A] mb-0.5">Role-Based Customization</p>
                After submitting, you will be guided through a 5-step role onboarding wizard to configure your ministry, designation, and competency targets.
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full bg-[#1E3A8A] hover:bg-[#1D3557] text-white font-semibold py-2.5 text-xs mt-2 rounded-lg shadow-sm transition-colors border border-[#1E3A8A]"
              >
                {loading ? "Creating Account..." : "Create Account & Proceed to Onboarding"}
              </Button>
            </form>
          </CardContent>

          <CardFooter className="pt-2 border-t border-slate-100 text-xs text-center justify-center">
            <span className="text-slate-600">
              Already have an official account?{" "}
              <a href="/login" className="font-semibold text-[#1E3A8A] hover:underline">
                Sign In
              </a>
            </span>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
