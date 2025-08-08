import React from 'react'

export const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="prose prose-lg max-w-none">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">Terms and Conditions</h1>
          
          <p className="text-gray-600 mb-8">
            <strong>Last updated:</strong> {new Date().toLocaleDateString()}
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Agreement to Terms</h2>
            <p className="text-gray-700 mb-4">
              By accessing and using the Linkware Consulting website and services, you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Description of Service</h2>
            <p className="text-gray-700 mb-4">
              Linkware Consulting provides IT solutions, educational content, and consulting services for capital markets professionals. Our platform offers:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Educational blog content and industry insights</li>
              <li>Premium membership services</li>
              <li>Consulting and technology solutions</li>
              <li>Community access and networking opportunities</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">User Accounts</h2>
            <p className="text-gray-700 mb-4">
              To access certain features of our service, you may be required to create an account. You agree to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Provide accurate and complete information</li>
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of any unauthorized use</li>
              <li>Accept responsibility for all activities under your account</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Acceptable Use</h2>
            <p className="text-gray-700 mb-4">
              You agree not to use our service to:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe on intellectual property rights</li>
              <li>Transmit harmful or malicious content</li>
              <li>Interfere with the proper functioning of the service</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Use the service for any commercial purpose without permission</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Intellectual Property</h2>
            <p className="text-gray-700 mb-4">
              All content on this website, including but not limited to text, graphics, logos, images, and software, is the property of Linkware Consulting or its content suppliers and is protected by copyright and other intellectual property laws.
            </p>
            <p className="text-gray-700 mb-4">
              You may not reproduce, distribute, modify, or create derivative works of our content without explicit written permission.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Payment and Subscriptions</h2>
            <p className="text-gray-700 mb-4">
              For premium services:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Payment is required in advance for subscription services</li>
              <li>Subscriptions automatically renew unless cancelled</li>
              <li>Refunds are subject to our refund policy</li>
              <li>We reserve the right to change pricing with notice</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Disclaimers</h2>
            <p className="text-gray-700 mb-4">
              The information on this website is provided on an "as is" basis. To the fullest extent permitted by law, Linkware Consulting:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Excludes all representations and warranties relating to this website and its contents</li>
              <li>Does not guarantee the accuracy, completeness, or timeliness of information</li>
              <li>Is not responsible for any investment decisions made based on our content</li>
              <li>Does not warrant that the website will be continuously available or error-free</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Limitation of Liability</h2>
            <p className="text-gray-700 mb-4">
              In no event shall Linkware Consulting be liable for any direct, indirect, incidental, special, or consequential damages arising out of or in connection with your use of our website or services, even if we have been advised of the possibility of such damages.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Termination</h2>
            <p className="text-gray-700 mb-4">
              We reserve the right to terminate or suspend your account and access to our services at our sole discretion, without notice, for conduct that we believe violates these Terms or is harmful to other users, us, or third parties.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Governing Law</h2>
            <p className="text-gray-700 mb-4">
              These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which Linkware Consulting operates, without regard to its conflict of law provisions.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Changes to Terms</h2>
            <p className="text-gray-700 mb-4">
              We reserve the right to modify these Terms at any time. We will notify users of any material changes by posting the updated Terms on our website. Your continued use of the service after such modifications constitutes acceptance of the updated Terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Contact Information</h2>
            <p className="text-gray-700 mb-4">
              If you have any questions about these Terms and Conditions, please contact us at:
            </p>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-700">
                <strong>Linkware Consulting</strong><br />
                Email: legal@linkware.com<br />
                Website: www.linkware.com
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
