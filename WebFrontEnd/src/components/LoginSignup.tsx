import { useEffect, useState } from 'react';
import { ArrowLeft, Mail, Lock, User, Zap, CheckCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import Loader from './ui/Loader.tsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

export default function LoginSignup({ onLogin, onBack }) {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [userType, setUserType] = useState('buyer');
  const [loginBtn, setLoginBtn] = useState(false);
  const [signInUser, setSignIn] = useState({
    fullName: 'John Doe',
    userEmail: 'you@example.com',
    userPassword: '',
    confirmedPassword: '',
    userName: '',
    firstName: '',
    lastName: '',
  });
  const [loginInUser, setLogin] = useState({
    userEmail: '',
    userPassword: '',
  });
  const [isLoading, setLoading] = useState(false);

  const features = [
    'Secure payment processing',
    'Real-time task tracking',
    '24/7 customer support',
    'Verified user community',
  ];

  useEffect(() => {
    if (loginBtn) {
      const loginAccount = async () => {
        try {
          const response = await fetch('http://127.0.0.1:8000/api/login/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              userEmail: loginInUser.userEmail,
              userPass: loginInUser.userPassword,
              user_Type: userType,
            }),
          });

          const data = await response.json();

          setTimeout(() => {
            if (response.status === 200) {
              alert('Login Successful');

              const user = {
                userName: data.firstName,
                email: data.email,
                userId: data.userId,
                role: data.role,
                isAdmin: data.isAdmin,
              };

              if (data.isAdmin) {
                onLogin('admin');
              } else if (data.role === 'seller') {
                onLogin('seller');
              } else {
                navigate('/buyer-dashboard', {
                  state: { userData: user },
                });
              }
            } else if (response.status === 400) {
              alert(data.error);
            } else {
              alert('Something went wrong');
            }

            setLoginBtn(false);
          }, 1000);
        } catch (error) {
          console.error(error);
          alert('Server connection failed');
        } finally {
          setLoading(false);
        }
      };

      loginAccount();
    }
  }, [loginBtn]);

  useEffect(() => {
    if (signInUser.userName !== '') {
      const createAccount = async () => {
        try {
          const response = await fetch('http://127.0.0.1:8000/api/signup/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              firstName: signInUser.firstName,
              lastName: signInUser.lastName,
              userEmail: signInUser.userEmail,
              userPass: signInUser.confirmedPassword,
              userName: signInUser.userName,
              user_Type: userType,
            }),
          });

          const data = await response.json();

          setTimeout(() => {
            if (response.status === 201) {
              alert('Account Created Successfully');
              window.location.reload();
            } else if (response.status === 400) {
              alert(data.error);
            } else if (response.status === 405) {
              alert('Invalid request method');
            } else {
              alert('Something went wrong');
            }
          }, 1000);

          setSignIn((prev) => ({
            ...prev,
            firstName: '',
            lastName: '',
            userName: '',
          }));
        } catch (error) {
          console.error(error);
          alert('Server connection failed');
        } finally {
          setLoading(false);
        }
      };

      createAccount();
    }
  }, [signInUser.userName]);

  const handleValidation = () => {
    if (!signInUser.fullName.trim()) {
      return { isTrue: false, message: 'UserName Field Is Empty' };
    }

    const nameRegex = /^[A-Za-z\s]+$/;
    if (!nameRegex.test(signInUser.fullName.trim())) {
      return { isTrue: false, message: 'Full Name cannot contain numbers or special characters.' };
    }

    if (!signInUser.userEmail.trim()) {
      return { isTrue: false, message: 'Email Field Is Empty' };
    }

    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    if (!emailRegex.test(signInUser.userEmail)) {
      return { isTrue: false, message: 'Enter a valid email address.' };
    }

    if (!signInUser.userPassword) {
      return { isTrue: false, message: 'Password Field Is Empty' };
    }

    if (signInUser.userPassword.length < 8) {
      return { isTrue: false, message: 'Password Is Too Short' };
    }

    if (signInUser.confirmedPassword !== signInUser.userPassword) {
      return { isTrue: false, message: 'Password Not Matched' };
    }

    return { isTrue: true, message: 'ok' };
  };

  const checkDigits = () => {
    for (let i = 0; i < 9; i++) {
      if (signInUser.userName.includes(i)) {
        return true;
      }
    }
    return false;
  };

  const generateUserName = () => {
    if (checkDigits()) {
      return;
    }
    const splitName = signInUser.fullName.trim().split(' ');
    const firstName = splitName[0] || '';
    const lastName = splitName[1] || '';
    const randomDigits = Math.floor(Math.random() * 900) + 100;
    setSignIn((prev) => ({
      ...prev,
      userName: (firstName + lastName).toLowerCase() + randomDigits,
      firstName,
      lastName,
    }));
  };

  const handleSignUp = () => {
    setLoading(true);
    const validationRespone = handleValidation();
    if (!validationRespone.isTrue) {
      alert(validationRespone.message);
      setLoading(false);
      return;
    }
    generateUserName();
  };

  const handleLogin = () => {
    setLoading(true);
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    if (!emailRegex.test(loginInUser.userEmail)) {
      alert('Enter a valid email address.');
      setLoading(false);
      return;
    }
    if (!loginInUser.userPassword) {
      alert('Password Field Is Empty');
      setLoading(false);
      return;
    }
    setLoginBtn(true);
  };

  return (
    <>
      {isLoading ? <Loader /> : (
        <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-green-50/30 flex items-center justify-center p-3 sm:p-4 md:p-6 lg:p-8">
          <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-6 lg:gap-8 items-center">
            <div className="hidden lg:block">
              <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                    <Zap className="w-7 h-7 text-white" />
                  </div>
                  <span className="text-gray-900">Engage X</span>
                </div>
                <h1 className="text-gray-900 mb-4">
                  {isLogin ? 'Welcome Back!' : 'Get Started Today'}
                </h1>
                <p className="text-gray-600 text-lg mb-8">
                  {isLogin
                    ? 'Sign in to continue growing your social media presence or earning money.'
                    : 'Join thousands of users already growing their brands and earning income.'}
                </p>
              </div>
              <div className="space-y-4">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    </div>
                    <span className="text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            <Card className="border-gray-200 rounded-2xl shadow-xl w-full">
              <CardHeader className="p-4 sm:p-6">
                <Button variant="ghost" size="sm" onClick={onBack} className="w-fit -ml-2 mb-4">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Home
                </Button>
                <CardTitle className="text-gray-900">
                  {isLogin ? 'Sign In' : 'Create Account'}
                </CardTitle>
                <CardDescription>
                  {isLogin ? 'Enter your credentials to access your account' : 'Fill in your information to get started'}
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                <Tabs value={isLogin ? 'login' : 'signup'} onValueChange={(v) => setIsLogin(v === 'login')}>
                  <TabsList className="w-full mb-6">
                    <TabsTrigger value="login" className="flex-1 text-sm sm:text-base">Login</TabsTrigger>
                    <TabsTrigger value="signup" className="flex-1 text-sm sm:text-base">Sign Up</TabsTrigger>
                  </TabsList>

                  <TabsContent value="login" className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="login-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input id="login-email" type="email" placeholder="you@example.com" className="pl-10" value={loginInUser.userEmail} onChange={(e) => setLogin((prev) => ({ ...prev, userEmail: e.target.value }))} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="login-password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input id="login-password" type="password" placeholder="********" className="pl-10" value={loginInUser.userPassword} onChange={(e) => setLogin((prev) => ({ ...prev, userPassword: e.target.value }))} />
                      </div>
                    </div>

                    <div className="space-y-3 pt-2">
                      <Label className="text-sm text-gray-600">Login as:</Label>
                      <div className="grid grid-cols-3 gap-2">
                        <Button type="button" variant={userType === 'buyer' ? 'default' : 'outline'} className={`rounded-full text-xs sm:text-sm px-2 sm:px-4 ${userType === 'buyer' ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white' : ''}`} onClick={() => setUserType('buyer')}>
                          Buyer
                        </Button>
                        <Button type="button" variant={userType === 'seller' ? 'default' : 'outline'} className={`rounded-full text-xs sm:text-sm px-2 sm:px-4 ${userType === 'seller' ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white' : ''}`} onClick={() => setUserType('seller')}>
                          Seller
                        </Button>
                        <Button type="button" variant={userType === 'admin' ? 'default' : 'outline'} className={`rounded-full text-xs sm:text-sm px-2 sm:px-4 ${userType === 'admin' ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white' : ''}`} onClick={() => setUserType('admin')}>
                          Admin
                        </Button>
                      </div>
                    </div>

                    <Button className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full" onClick={handleLogin}>
                      Sign In
                    </Button>
                  </TabsContent>

                  <TabsContent value="signup" className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="signup-name">Full Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input id="signup-name" type="text" placeholder="John Doe" className="pl-10" onChange={(e) => setSignIn((prev) => ({ ...prev, fullName: e.target.value }))} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signup-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input id="signup-email" type="email" placeholder="you@example.com" className="pl-10" onChange={(e) => setSignIn((prev) => ({ ...prev, userEmail: e.target.value }))} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="signup-password">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input id="signup-password" type="password" placeholder="********" className="pl-10" onChange={(e) => setSignIn((prev) => ({ ...prev, userPassword: e.target.value }))} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="confirm-password">Confirm Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <Input id="confirm-password" type="password" placeholder="********" className="pl-10" onChange={(e) => setSignIn((prev) => ({ ...prev, confirmedPassword: e.target.value }))} />
                      </div>
                    </div>

                    <div className="space-y-3 pt-2">
                      <Label className="text-sm text-gray-600">I want to:</Label>
                      <div className="grid grid-cols-2 gap-2">
                        <Button type="button" variant={userType === 'buyer' ? 'default' : 'outline'} className={`rounded-full text-xs sm:text-sm ${userType === 'buyer' ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white' : ''}`} onClick={() => setUserType('buyer')}>
                          Buy Tasks
                        </Button>
                        <Button type="button" variant={userType === 'seller' ? 'default' : 'outline'} className={`rounded-full text-xs sm:text-sm ${userType === 'seller' ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white' : ''}`} onClick={() => setUserType('seller')}>
                          Earn Money
                        </Button>
                      </div>
                    </div>

                    <div className="text-xs text-gray-500">
                      By signing up, you agree to our <a href="#" className="text-green-600 hover:text-green-700">Terms of Service</a> and <a href="#" className="text-green-600 hover:text-green-700">Privacy Policy</a>
                    </div>

                    <Button className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-full" onClick={handleSignUp}>
                      Create Account
                    </Button>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
