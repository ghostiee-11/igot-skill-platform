"use client";

import React, { useState } from "react";
import { Mail, ArrowLeft, CheckCircle2, Award } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { fetchApi } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await fetchApi("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      setSubmitted(true);
    } catch {
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="inline-flex h-12 w-12 rounded-xl bg-[#1E3A8A] text-white items-center justify-center mb-3 shadow-sm">
            <Award className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Reset Password</h2>
          <p className="text-xs text-slate-500 mt-1">Official Karmayogi Credential Recovery</p>
        </div>

        <Card className="border-slate-200 shadow-sm bg-white">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900">Forgot your credentials?</CardTitle>
            <CardDescription className="text-xs">
              Enter your official government email to receive password recovery instructions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {submitted ? (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex flex-col items-center text-center gap-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                <p className="font-semibold text-sm">Recovery Link Sent</p>
                <p className="text-slate-600">
                  If an account exists for <span className="font-semibold text-slate-800">{email}</span>, a secure password reset token has been dispatched.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Official Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@mospi.gov.in"
                      className="pl-9 text-xs"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={loading} className="w-full bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs cursor-pointer">
                  {loading ? "Sending..." : "Send Password Reset Link"}
                </Button>
              </form>
            )}
          </CardContent>
          <CardFooter className="justify-center border-t border-slate-100 pt-3">
            <a href="/login" className="inline-flex items-center text-xs font-semibold text-slate-600 hover:text-slate-900">
              <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Back to Sign In
            </a>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
