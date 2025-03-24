"use client";

import React from "react";
import Link from "next/link";

const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center font-inter">
      {/* Header */}
      <header className="w-full py-4 border-b border-gray-200">
        <div className="container mx-auto px-4 flex flex-col items-center">
          <h1 className="text-4xl font-extrabold text-gray-900">Pcap Analyzer</h1>
          <p className="mt-1 text-lg text-gray-600">
            Unlocking Insights from .pcapng Files
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-12 flex flex-col items-center text-center">
        {/* Hero Section */}
        <section className="max-w-3xl">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Transform Your Network Data into Actionable Insights
          </h2>
          <p className="mb-8 text-xl text-gray-700">
            Our innovative platform empowers you to upload and analyze .pcapng files effortlessly. 
            Discover detailed packet characteristics, monitor network behavior, and gain the insights you need to optimize your systems.
          </p>
          <Link
            href="/dashboard"
            className="inline-block bg-gray-900 text-white py-3 px-6 rounded-full text-xl font-semibold shadow-md hover:bg-gray-800 transition duration-300"
          >
            Get Started
          </Link>
        </section>

        {/* Features Section */}
        <section className="mt-16 max-w-4xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="text-2xl font-bold mb-3 text-gray-900">
                Deep Packet Inspection
              </h3>
              <p className="text-gray-600">
                Examine every detail of your network traffic – from protocols to data payloads.
              </p>
            </div>
            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="text-2xl font-bold mb-3 text-gray-900">
                Real-Time Analytics
              </h3>
              <p className="text-gray-600">
                Visualize trends and detect anomalies with our dynamic, real-time dashboard.
              </p>
            </div>
            <div className="bg-white rounded-xl shadow p-6">
              <h3 className="text-2xl font-bold mb-3 text-gray-900">
                Comprehensive Reporting
              </h3>
              <p className="text-gray-600">
                Generate concise, actionable reports to drive informed decisions.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full py-4 border-t border-gray-200">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-600">
            &copy; {new Date().getFullYear()} Pcap Analyzer. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
