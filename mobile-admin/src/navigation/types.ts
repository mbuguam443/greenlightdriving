import { NavigatorScreenParams } from '@react-navigation/native';

export type AuthStackParamList = {
  Login: undefined;
};

export type AdminStackParamList = {
  Dashboard: undefined;
  Students: undefined;
  StudentDetail: { studentId: number };
  Payments: undefined;
  Lessons: undefined;
  Admissions: undefined;
  Notifications: undefined;
  Documents: undefined;
  Enquiries: undefined;
  Chat: undefined;
  Profile: undefined;
};

export type AppTabsParamList = {
  HomeTab: undefined;
  StudentsTab: undefined;
  AdmissionsTab: undefined;
  MoreTab: NavigatorScreenParams<MoreStackParamList>;
};

export type MoreStackParamList = {
  More: undefined;
  Payments: undefined;
  Lessons: undefined;
  Notifications: undefined;
  Documents: undefined;
  Enquiries: undefined;
  Chat: undefined;
  Profile: undefined;
};

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  App: NavigatorScreenParams<AppTabsParamList>;
};
